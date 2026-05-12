from uuid import uuid4

from app.audits.models import Audit
from app.audits.schemas import AuditBatchRequest, AuditRead, AuditRunRequest
from app.business_rules.models import BusinessRule
from app.cases.models import Case, CaseDocument
from app.cases.service import infer_document_type, resolve_case
from app.core.exceptions import AppError, NotFoundError
from app.shared.ai_service import AIService
from app.shared.enums import CaseStatus, DocumentType, RuleStatus, RuleType
from app.shared.schemas import public_id, utc_now
from app.users.models import User

BASE_REQUIRED_DOCUMENT_TYPES = {
    DocumentType.FACTURA,
    DocumentType.ORDEN_REPARACION,
    DocumentType.DETALLE_MANO_OBRA,
    DocumentType.FOTOS_DANIO,
}


def audit_to_read(audit: Audit) -> AuditRead:
    return AuditRead(
        audit_id=audit.audit_id,
        case_id=audit.case_claim_number or public_id(audit.case_id),
        status=audit.status,
        risk_score=audit.risk_score,
        confidence=audit.confidence,
        summary=audit.summary,
        invoice_total=audit.invoice_total,
        expected_total=audit.expected_total,
        difference=audit.difference,
        findings=audit.findings,
        discrepancies=audit.discrepancies,
        top_reasons=audit.top_reasons,
        recommendation=audit.recommendation,
        documents=audit.documents,
        final_verdict=audit.final_verdict,
        created_at=audit.created_at,
    )


async def run_audit(case_id: str, payload: AuditRunRequest, current_user: User | None) -> AuditRead:
    case = await resolve_case(case_id)
    case.status = CaseStatus.EN_AUDITORIA
    case.updated_at = utc_now()
    await case.save()

    audit = await _execute_audit(case, payload, current_user, is_final=False)
    return audit_to_read(audit)


async def run_batch_audit(payload: AuditBatchRequest, current_user: User | None) -> list[AuditRead]:
    if len(payload.case_ids) > 5:
        raise AppError("La auditoria por lote admite maximo 5 casos.")

    results = []
    for case_id in payload.case_ids:
        results.append(await run_audit(case_id, AuditRunRequest(source="batch"), current_user))
    return results


async def run_final_verdict(case_id: str, current_user: User | None) -> AuditRead:
    case = await resolve_case(case_id)
    audit = await _execute_audit(case, AuditRunRequest(source="final-verdict"), current_user, is_final=True)
    return audit_to_read(audit)


async def get_latest_audit(case_id: str) -> AuditRead:
    case = await resolve_case(case_id)
    audit = await Audit.find(Audit.case_id == case.id).sort("-created_at").first_or_none()
    if not audit:
        raise NotFoundError("Este caso aun no tiene auditoria registrada.")
    return audit_to_read(audit)


async def get_audit_history(case_id: str) -> list[AuditRead]:
    case = await resolve_case(case_id)
    audits = await Audit.find(Audit.case_id == case.id).sort("-created_at").to_list()
    return [audit_to_read(item) for item in audits]


async def _execute_audit(case: Case, payload: AuditRunRequest, current_user: User | None, is_final: bool) -> Audit:
    documents = await CaseDocument.find(CaseDocument.case_id == case.id).sort("-uploaded_at").to_list()
    active_rules = await BusinessRule.find(BusinessRule.status == RuleStatus.ACTIVA).to_list()
    context = _build_audit_context(case, documents, active_rules, payload, is_final)

    effective_documents = _effective_documents(documents)
    discrepancies = _evaluate_documents(case, effective_documents)
    missing_types = {item.get("document_type") for item in discrepancies if item.get("type") == "DOCUMENTO_FALTANTE"}
    discrepancies.extend(_evaluate_business_rules(active_rules, effective_documents, missing_types))
    discrepancies.extend(_evaluate_financials(case))
    discrepancies.extend(_evaluate_text_consistency(case, effective_documents))

    ai_result = await AIService().audit_case(context)
    discrepancies.extend(_normalize_ai_discrepancies(ai_result.get("discrepancies", [])))
    discrepancies = _dedupe_discrepancies(discrepancies)

    findings = _findings_from_discrepancies(discrepancies)
    top_reasons = _top_reasons(discrepancies)
    risk_score = _risk_score(discrepancies)
    status = _status_from_score_and_discrepancies(risk_score, discrepancies)
    summary = ai_result.get("summary") or _summary_for_status(status, discrepancies, is_final)
    recommendation = ai_result.get("recommendation") or _recommendation_for_status(status, is_final)
    final_verdict = _final_verdict(status, recommendation) if is_final else None

    audit = Audit(
        audit_id=f"AUD-{uuid4().hex[:10].upper()}",
        case_id=case.id,
        case_claim_number=case.claim_number,
        status=status,
        risk_score=risk_score,
        confidence=max(0, round((100 - risk_score) / 100, 2)),
        summary=summary,
        invoice_total=case.invoice_total,
        expected_total=case.tariff_total,
        difference=_difference(case),
        findings=findings,
        discrepancies=discrepancies,
        top_reasons=top_reasons,
        recommendation=recommendation,
        documents=[_document_snapshot(item) for item in effective_documents],
        final_verdict=final_verdict,
        is_final=is_final,
        executed_by=current_user.id if current_user else None,
        source=payload.source,
    )
    await audit.insert()

    case.status = status
    case.confidence = max(0, 100 - risk_score)
    case.findings = findings
    case.updated_at = utc_now()
    await case.save()
    return audit


def _build_audit_context(
    case: Case,
    documents: list[CaseDocument],
    rules: list[BusinessRule],
    payload: AuditRunRequest,
    is_final: bool,
) -> dict:
    return {
        "case": {
            "claimNumber": case.claim_number,
            "workshop": case.workshop,
            "vehicle": case.vehicle,
            "plate": case.plate,
            "reportedDamages": case.reported_damages,
            "invoiceTotal": case.invoice_total,
            "tariffTotal": case.tariff_total,
        },
        "documents": [_document_snapshot(document, include_text=True) for document in documents],
        "businessRules": [
            {
                "name": rule.name,
                "description": rule.description,
                "type": rule.type.value,
                "targetField": rule.target_field,
                "operator": rule.operator.value,
                "referenceValue": rule.reference_value,
                "severity": rule.severity.value,
                "alertMessage": rule.alert_message,
            }
            for rule in rules
        ],
        "payload": payload.model_dump(mode="json"),
        "isFinalVerdict": is_final,
    }


def _evaluate_documents(case: Case, documents: list[CaseDocument]) -> list[dict]:
    discrepancies = []
    uploaded_types = {document.document_type for document in documents}
    required_types = set(BASE_REQUIRED_DOCUMENT_TYPES)

    if case.tariff_total is not None:
        required_types.add(DocumentType.TARIFARIO)

    for document_type in sorted(required_types - uploaded_types):
        discrepancies.append(_discrepancy(
            type_="DOCUMENTO_FALTANTE",
            message=f"Falta documento obligatorio: {document_type.value}.",
            severity="ALTA",
            document_type=document_type.value,
        ))

    for document in documents:
        if document.parse_status.value == "ERROR":
            discrepancies.append(_discrepancy(
                type_="ERROR_PARSE_DOCUMENTO",
                message=f"No se pudo procesar el documento {document.original_name or document.name}.",
                severity="MEDIA",
                document_id=public_id(document.id),
            ))
        if document.parse_status.value == "OCR_PENDIENTE":
            discrepancies.append(_discrepancy(
                type_="OCR_PENDIENTE",
                message=f"El documento {document.original_name or document.name} requiere OCR para validar contenido.",
                severity="MEDIA",
                document_id=public_id(document.id),
            ))

    return discrepancies


def _evaluate_business_rules(rules: list[BusinessRule], documents: list[CaseDocument], known_missing_types: set[str | None]) -> list[dict]:
    discrepancies = []
    document_types = {item.document_type.value for item in documents}

    for rule in rules:
        if rule.type == RuleType.DOCUMENTO_OBLIGATORIO and rule.reference_value:
            required_type = rule.reference_value.strip().upper()
            if required_type in known_missing_types:
                continue
            if required_type and required_type not in document_types:
                discrepancies.append(_discrepancy(
                    type_=rule.type.value,
                    message=rule.alert_message,
                    severity=rule.severity.value,
                    rule_id=public_id(rule.id),
                ))

    return discrepancies


def _evaluate_financials(case: Case) -> list[dict]:
    if case.invoice_total is None or case.tariff_total is None:
        return [_discrepancy(
            type_="DATO_FINANCIERO_FALTANTE",
            message="Dato no disponible: invoiceTotal o tariffTotal.",
            severity="MEDIA",
        )]

    difference = case.invoice_total - case.tariff_total
    if difference <= 0:
        return []

    ratio = difference / case.tariff_total if case.tariff_total else 1
    if ratio <= 0.1:
        severity = "BAJA"
    elif ratio <= 0.25:
        severity = "MEDIA"
    elif ratio <= 0.4:
        severity = "ALTA"
    else:
        severity = "CRITICA"
    return [_discrepancy(
        type_="DIFERENCIA_FINANCIERA",
        message="La factura supera el valor esperado por tarifario.",
        severity=severity,
        expected=case.tariff_total,
        found=case.invoice_total,
        difference=round(difference, 2),
    )]


def _evaluate_text_consistency(case: Case, documents: list[CaseDocument]) -> list[dict]:
    text = "\n".join(document.extracted_text.lower() for document in documents if document.extracted_text)
    if not text:
        return []

    discrepancies = []
    for damage in case.reported_damages:
        if damage and damage.lower() not in text:
            discrepancies.append(_discrepancy(
                type_="ITEM_NO_RELACIONADO",
                message=f"No se encontro sustento textual para el dano reportado: {damage}.",
                severity="MEDIA",
                item=damage,
            ))

    duplicate_terms = ["duplicado", "doble cobro", "repetido"]
    if any(term in text for term in duplicate_terms):
        discrepancies.append(_discrepancy(
            type_="POSIBLE_DUPLICADO",
            message="Se detectaron indicios textuales de cobro duplicado.",
            severity="ALTA",
        ))

    return discrepancies


def _normalize_ai_discrepancies(items: list) -> list[dict]:
    if not isinstance(items, list):
        return []
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        message = item.get("message") or item.get("descripcion") or item.get("description")
        type_ = item.get("type") or item.get("tipo")
        if not _has_meaningful_text(message) or not _has_meaningful_text(type_):
            continue
        normalized.append(_discrepancy(
            type_=str(type_).upper(),
            message=str(message),
            severity=item.get("severity") or item.get("severidad") or "MEDIA",
            expected=item.get("expected") or item.get("valor_esperado"),
            found=item.get("found") or item.get("valor_encontrado"),
        ))
    return normalized


def _status_from_score_and_discrepancies(risk_score: int, discrepancies: list[dict]) -> CaseStatus:
    critical_financial_or_coverage = any(
        item.get("severity") == "CRITICA"
        and item.get("type") in {"DIFERENCIA_FINANCIERA", "FUERA_DE_COBERTURA", "PRECIO_MAXIMO"}
        for item in discrepancies
    )
    if critical_financial_or_coverage:
        return CaseStatus.DENEGADO
    if risk_score >= 70:
        return CaseStatus.REVISION_HUMANA
    if discrepancies:
        return CaseStatus.OBSERVADO
    return CaseStatus.APROBADO


def _risk_score(discrepancies: list[dict]) -> int:
    weights = {"BAJA": 5, "MEDIA": 10, "ALTA": 18, "CRITICA": 35}
    return min(100, sum(weights.get(item.get("severity", "MEDIA"), 15) for item in discrepancies))


def _findings_from_discrepancies(discrepancies: list[dict]) -> list[dict]:
    return [
        {
            "id": f"FND-{index + 1}",
            "title": item.get("type", "Dato no disponible"),
            "detail": item.get("message", "Dato no disponible"),
            "severity": item.get("severity", "MEDIA"),
            "impact": item.get("difference"),
        }
        for index, item in enumerate(discrepancies)
    ]


def _top_reasons(discrepancies: list[dict]) -> list[str]:
    reasons = []
    for item in discrepancies:
        reason = item.get("message") or item.get("type") or "Dato no disponible"
        if not _has_meaningful_text(reason):
            continue
        if reason not in reasons:
            reasons.append(reason)
    return reasons[:5]


def _summary_for_status(status: CaseStatus, discrepancies: list[dict], is_final: bool) -> str:
    prefix = "Veredicto final" if is_final else "Auditoria"
    if status == CaseStatus.APROBADO:
        return f"{prefix} completado sin discrepancias criticas."
    return f"{prefix} completado con {len(discrepancies)} hallazgo(s)."


def _recommendation_for_status(status: CaseStatus, is_final: bool) -> str:
    if status == CaseStatus.APROBADO:
        return "Continuar con el flujo de aprobacion."
    if status == CaseStatus.DENEGADO:
        return "No aprobar hasta corregir discrepancias criticas y sustento documental."
    if status == CaseStatus.REVISION_HUMANA:
        return "Enviar a revision humana con trazabilidad documental."
    if is_final:
        return "Revisar sustento adicional antes de emitir aprobacion definitiva."
    return "Solicitar sustento adicional y revisar discrepancias."


def _final_verdict(status: CaseStatus, recommendation: str) -> str:
    return f"{status.value}: {recommendation}"


def _difference(case: Case) -> float | None:
    if case.invoice_total is None or case.tariff_total is None:
        return None
    return round(case.invoice_total - case.tariff_total, 2)


def _document_snapshot(document: CaseDocument, include_text: bool = False) -> dict:
    snapshot = {
        "id": public_id(document.id),
        "type": document.document_type.value,
        "originalName": document.original_name or document.name,
        "mimeType": document.mime_type,
        "size": document.size,
        "parseStatus": document.parse_status.value,
        "uploadedAt": document.uploaded_at.isoformat(),
    }
    if include_text:
        snapshot["extractedText"] = document.extracted_text[:3000] if document.extracted_text else "Dato no disponible"
    return snapshot


def _discrepancy(type_: str, message: str, severity: str, **extra) -> dict:
    return {
        "type": type_,
        "message": message,
        "severity": severity,
        **extra,
    }


def _effective_documents(documents: list[CaseDocument]) -> list[CaseDocument]:
    for document in documents:
        document.document_type = infer_document_type(document.original_name or document.name, document.document_type)
    return documents


def _dedupe_discrepancies(discrepancies: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in discrepancies:
        key = (
            item.get("type"),
            item.get("message"),
            item.get("document_type"),
            item.get("rule_id"),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _has_meaningful_text(value: object) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"dato no disponible", "n/a", "na", "none", "null", "-"}

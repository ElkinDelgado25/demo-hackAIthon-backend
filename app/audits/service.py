from uuid import uuid4

from app.audits.models import Audit
from app.audits.schemas import AuditRead, AuditRunRequest
from app.business_rules.models import BusinessRule
from app.cases.models import CaseDocument
from app.cases.service import ensure_required_documents, resolve_case
from app.core.exceptions import NotFoundError
from app.shared.enums import CaseStatus, RuleStatus, RuleType
from app.shared.schemas import public_id, utc_now
from app.users.models import User


def audit_to_read(audit: Audit) -> AuditRead:
    return AuditRead(
        audit_id=audit.audit_id,
        case_id=audit.case_claim_number,
        status=audit.status,
        confidence=audit.confidence,
        summary=audit.summary,
        discrepancies=audit.discrepancies,
        recommendation=audit.recommendation,
        documents=audit.documents,
        created_at=audit.created_at,
    )


async def run_audit(case_id: str, payload: AuditRunRequest, current_user: User | None) -> AuditRead:
    case = await resolve_case(case_id)
    case.status = CaseStatus.EN_AUDITORIA
    case.updated_at = utc_now()
    await case.save()

    documents = await ensure_required_documents(case)
    active_rules = await BusinessRule.find(BusinessRule.status == RuleStatus.ACTIVA).to_list()
    discrepancies = _evaluate_rules(active_rules, documents)

    status = _status_from_discrepancies(discrepancies)
    confidence = 0 if not documents else max(0.0, 1.0 - (len(discrepancies) * 0.12))
    summary = _summary_for_status(status, discrepancies)
    recommendation = _recommendation_for_status(status)

    audit = Audit(
        audit_id=f"AUD-{uuid4().hex[:10].upper()}",
        case_id=case.id,
        case_claim_number=case.claim_number,
        status=status,
        confidence=round(confidence, 2),
        summary=summary,
        discrepancies=discrepancies,
        recommendation=recommendation,
        documents=[_document_snapshot(item) for item in documents],
        executed_by=current_user.id if current_user else None,
        source=payload.source,
    )
    await audit.insert()

    case.status = status
    case.confidence = round(confidence * 100)
    case.findings = [
        {"id": f"FND-{index + 1}", "title": item["type"], "detail": item["message"], "impact": None}
        for index, item in enumerate(discrepancies)
    ]
    case.updated_at = utc_now()
    await case.save()
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


def _evaluate_rules(rules: list[BusinessRule], documents: list[CaseDocument]) -> list[dict[str, str]]:
    discrepancies: list[dict[str, str]] = []
    document_types = {item.document_type.value for item in documents}

    for rule in rules:
        if rule.type == RuleType.DOCUMENTO_OBLIGATORIO and rule.reference_value:
            required_type = rule.reference_value.strip().upper()
            if required_type and required_type not in document_types:
                discrepancies.append(
                    {
                        "type": rule.type.value,
                        "message": rule.alert_message,
                        "severity": rule.severity.value,
                        "ruleId": public_id(rule.id),
                    }
                )

    return discrepancies


def _status_from_discrepancies(discrepancies: list[dict[str, str]]) -> CaseStatus:
    if any(item.get("severity") == "CRITICA" for item in discrepancies):
        return CaseStatus.DENEGADO
    if discrepancies:
        return CaseStatus.OBSERVADO
    return CaseStatus.APROBADO


def _summary_for_status(status: CaseStatus, discrepancies: list[dict[str, str]]) -> str:
    if status == CaseStatus.APROBADO:
        return "Auditoria completada sin discrepancias registradas."
    return f"Auditoria completada con {len(discrepancies)} discrepancia(s)."


def _recommendation_for_status(status: CaseStatus) -> str:
    if status == CaseStatus.APROBADO:
        return "Continuar con el flujo de aprobacion."
    if status == CaseStatus.DENEGADO:
        return "Revisar razones de negacion y solicitar soporte adicional."
    return "Revisar discrepancias antes de aprobar el caso."


def _document_snapshot(document: CaseDocument) -> dict[str, str | int]:
    return {
        "id": public_id(document.id),
        "name": document.name,
        "type": document.document_type.value,
        "size": document.size,
        "mimeType": document.mime_type,
    }

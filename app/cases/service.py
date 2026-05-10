import json
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.cases.models import Case, CaseDocument
from app.cases.schemas import CaseCreate, CaseRead, DocumentMetadata, DocumentRead
from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.shared.enums import CaseStatus, DocumentType
from app.shared.schemas import public_id, utc_now
from app.users.models import User

REQUIRED_DOCUMENT_TYPES = {
    DocumentType.FACTURA,
    DocumentType.ORDEN_REPARACION,
    DocumentType.DETALLE_MANO_OBRA,
    DocumentType.FOTOS_DANIO,
}


def case_to_read(case: Case) -> CaseRead:
    return CaseRead(
        id=public_id(case.id),
        claim_number=case.claim_number,
        workshop=case.workshop,
        vehicle=case.vehicle,
        plate=case.plate,
        reported_damages=case.reported_damages,
        invoice_total=case.invoice_total,
        tariff_total=case.tariff_total,
        status=case.status,
        confidence=case.confidence,
        findings=case.findings,
        received_at=case.received_at,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


def document_to_read(document: CaseDocument) -> DocumentRead:
    return DocumentRead(
        id=public_id(document.id),
        case_id=document.case_claim_number,
        document_type=document.document_type,
        name=document.name,
        size=document.size,
        type=document.extension,
        mime_type=document.mime_type,
        uploaded_at=document.uploaded_at,
        status=document.status,
        extraction_status=document.extraction_status,
    )


async def list_cases() -> list[CaseRead]:
    cases = await Case.find_all().sort("-received_at", "-updated_at").to_list()
    return [case_to_read(item) for item in cases]


async def create_case(payload: CaseCreate) -> CaseRead:
    existing = await Case.find_one(Case.claim_number == payload.claim_number)
    if existing:
        raise ConflictError("Ya existe un caso con ese numero de siniestro.")

    case = Case(**payload.model_dump())
    await case.insert()
    return case_to_read(case)


async def resolve_case(case_id: str) -> Case:
    case = await Case.find_one(Case.claim_number == case_id)
    if case:
        return case

    try:
        by_id = await Case.get(case_id)
    except Exception:
        by_id = None

    if not by_id:
        raise NotFoundError("Caso no encontrado.")
    return by_id


async def get_case(case_id: str) -> CaseRead:
    return case_to_read(await resolve_case(case_id))


async def update_case_status(case_id: str, status: CaseStatus) -> CaseRead:
    case = await resolve_case(case_id)
    case.status = status
    case.updated_at = utc_now()
    await case.save()
    return case_to_read(case)


async def list_documents(case_id: str) -> list[DocumentRead]:
    case = await resolve_case(case_id)
    documents = await CaseDocument.find(CaseDocument.case_id == case.id).sort("-uploaded_at").to_list()
    return [document_to_read(item) for item in documents]


async def upload_documents(case_id: str, files: list[UploadFile], documents_json: str, current_user: User | None) -> list[DocumentRead]:
    case = await resolve_case(case_id)
    metadata = _parse_metadata(documents_json)
    if len(metadata) != len(files):
        raise AppError("La metadata de documentos no coincide con los archivos enviados.")

    existing_documents = await CaseDocument.find(CaseDocument.case_id == case.id).to_list()
    existing_total = sum(item.size for item in existing_documents)
    incoming_total = sum(item.size for item in metadata)
    if existing_total + incoming_total > settings.upload_max_total_bytes:
        raise AppError("El total de documentos supera el maximo permitido.", status_code=413)

    storage_dir = settings.upload_local_dir / case.claim_number
    storage_dir.mkdir(parents=True, exist_ok=True)
    saved_documents: list[CaseDocument] = []

    for upload_file, item in zip(files, metadata, strict=True):
        extension = Path(item.name or upload_file.filename or "").suffix.lower().lstrip(".")
        if extension not in settings.allowed_extensions:
            raise AppError(f"Tipo de archivo no permitido: {extension}.")

        safe_name = f"{uuid4().hex}.{extension}"
        storage_path = storage_dir / safe_name
        content = await upload_file.read()
        if len(content) != item.size:
            item.size = len(content)
        storage_path.write_bytes(content)

        document = CaseDocument(
            case_id=case.id,
            case_claim_number=case.claim_number,
            document_type=item.type,
            name=item.name,
            size=item.size,
            mime_type=item.mime_type,
            extension=extension,
            storage_path=str(storage_path),
            uploaded_by=current_user.id if current_user else None,
        )
        await document.insert()
        saved_documents.append(document)

    case.status = CaseStatus.LISTO_PARA_AUDITORIA
    case.updated_at = utc_now()
    await case.save()
    return [document_to_read(item) for item in saved_documents]


async def ensure_required_documents(case: Case) -> list[CaseDocument]:
    documents = await CaseDocument.find(CaseDocument.case_id == case.id).to_list()
    uploaded_types = {item.document_type for item in documents}
    missing = sorted(REQUIRED_DOCUMENT_TYPES - uploaded_types)
    if missing:
        raise AppError(f"Faltan documentos obligatorios: {', '.join(missing)}.")
    return documents


def _parse_metadata(documents_json: str) -> list[DocumentMetadata]:
    try:
        raw_items = json.loads(documents_json)
    except json.JSONDecodeError as exc:
        raise AppError("La metadata de documentos no es JSON valido.") from exc
    if not isinstance(raw_items, list):
        raise AppError("La metadata de documentos debe ser una lista.")
    return [DocumentMetadata.model_validate(item) for item in raw_items]

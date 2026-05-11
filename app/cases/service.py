import json
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.cases.models import Case, CaseDocument
from app.cases.schemas import CaseCreate, CaseRead, DocumentMetadata, DocumentRead
from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.shared.enums import CaseStatus, DocumentType, ParseStatus
from app.shared.file_parser import FileParser
from app.shared.schemas import public_id, utc_now
from app.users.models import User

REQUIRED_DOCUMENT_TYPES = {
    DocumentType.FACTURA,
    DocumentType.ORDEN_REPARACION,
    DocumentType.DETALLE_MANO_OBRA,
    DocumentType.FOTOS_DANIO,
}

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}


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
        type=document.document_type,
        name=document.original_name or document.name,
        original_name=document.original_name or document.name,
        size=document.size,
        extension=document.extension,
        mime_type=document.mime_type,
        uploaded_at=document.uploaded_at,
        status=document.status,
        parse_status=document.parse_status,
        parse_error=document.parse_error,
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

    saved_documents: list[CaseDocument] = []
    parser = FileParser()

    for upload_file, item in zip(files, metadata, strict=True):
        original_name = _safe_original_name(item.name or upload_file.filename or "documento")
        extension = Path(original_name).suffix.lower().lstrip(".")
        if extension not in settings.allowed_extensions:
            raise AppError(f"Tipo de archivo no permitido: {extension}.")

        document_id = f"doc_{uuid4().hex[:12]}"
        safe_name = f"{Path(original_name).stem[:80] or 'documento'}_{uuid4().hex[:8]}.{extension}"
        storage_dir = settings.upload_local_dir / case.claim_number / document_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_path = (storage_dir / safe_name).resolve()
        _ensure_storage_path(storage_path)

        content = await upload_file.read()
        if len(content) != item.size:
            item.size = len(content)
        storage_path.write_bytes(content)

        parse_status = ParseStatus.OCR_PENDIENTE if extension in IMAGE_EXTENSIONS else ParseStatus.PROCESANDO
        parse_error = None
        extracted_text = ""
        if extension not in IMAGE_EXTENSIONS:
            try:
                extracted_text = await parser.parse(content, original_name)
                parse_status = ParseStatus.PROCESADO
            except Exception as exc:
                parse_status = ParseStatus.ERROR
                parse_error = str(exc)

        document = CaseDocument(
            case_id=case.id,
            case_claim_number=case.claim_number,
            document_type=item.type,
            name=safe_name,
            original_name=original_name,
            size=item.size,
            mime_type=item.mime_type,
            extension=extension,
            storage_path=str(storage_path),
            extracted_text=extracted_text,
            parse_status=parse_status,
            parse_error=parse_error,
            extraction_status=parse_status.value,
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


def _safe_original_name(filename: str) -> str:
    name = Path(filename).name.strip().replace("\\", "_").replace("/", "_")
    if not name or name in {".", ".."}:
        raise AppError("Nombre de archivo invalido.")
    return "".join(char for char in name if char.isalnum() or char in {" ", ".", "_", "-"}).strip() or "documento"


def _ensure_storage_path(path: Path) -> None:
    storage_root = settings.upload_local_dir.resolve()
    if storage_root not in path.parents:
        raise AppError("Ruta de almacenamiento invalida.")

from datetime import datetime
from typing import Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field

from app.shared.enums import CaseStatus, DocumentType
from app.shared.schemas import utc_now


class Case(Document):
    claim_number: Indexed(str, unique=True)
    workshop: str | None = None
    vehicle: dict[str, Any] = Field(default_factory=dict)
    plate: str | None = None
    reported_damages: list[str] = Field(default_factory=list)
    invoice_total: float | None = None
    tariff_total: float | None = None
    status: CaseStatus = CaseStatus.NUEVO
    confidence: float | None = None
    findings: list[dict[str, Any]] = Field(default_factory=list)
    received_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "cases"


class CaseDocument(Document):
    case_id: PydanticObjectId
    case_claim_number: str
    document_type: DocumentType
    name: str
    size: int
    mime_type: str
    extension: str
    storage_path: str
    status: str = "cargado"
    extraction_status: str | None = "pendiente"
    uploaded_by: PydanticObjectId | None = None
    uploaded_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "case_documents"

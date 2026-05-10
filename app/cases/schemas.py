from datetime import datetime
from typing import Any

from pydantic import Field

from app.shared.enums import CaseStatus, DocumentType
from app.shared.schemas import ApiModel


class CaseCreate(ApiModel):
    claim_number: str = Field(min_length=1, max_length=80)
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


class CaseStatusUpdate(ApiModel):
    status: CaseStatus


class CaseRead(ApiModel):
    id: str
    claim_number: str
    workshop: str | None = None
    vehicle: dict[str, Any] = Field(default_factory=dict)
    plate: str | None = None
    reported_damages: list[str] = Field(default_factory=list)
    invoice_total: float | None = None
    tariff_total: float | None = None
    status: CaseStatus
    confidence: float | None = None
    findings: list[dict[str, Any]] = Field(default_factory=list)
    received_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CaseListResponse(ApiModel):
    cases: list[CaseRead]


class DocumentMetadata(ApiModel):
    name: str
    type: DocumentType
    size: int
    mime_type: str = "application/octet-stream"


class DocumentRead(ApiModel):
    id: str
    case_id: str
    document_type: DocumentType
    name: str
    size: int
    type: str
    mime_type: str
    uploaded_at: datetime
    status: str
    extraction_status: str | None = None


class DocumentsResponse(ApiModel):
    documents: list[DocumentRead]

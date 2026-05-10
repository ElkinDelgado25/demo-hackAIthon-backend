from datetime import datetime
from typing import Any

from pydantic import Field

from app.shared.enums import CaseStatus
from app.shared.schemas import ApiModel


class AuditRunRequest(ApiModel):
    case_id: str | None = None
    vehicle: dict[str, Any] = Field(default_factory=dict)
    reported_damages: list[str] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    requested_by: str | None = None
    source: str | None = None


class AuditRead(ApiModel):
    audit_id: str
    case_id: str
    status: CaseStatus
    confidence: float
    summary: str
    discrepancies: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str | None = None
    documents: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime


class AuditHistoryResponse(ApiModel):
    history: list[AuditRead]

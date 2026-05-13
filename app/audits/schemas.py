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


class AuditBatchRequest(ApiModel):
    case_ids: list[str] = Field(min_length=1, max_length=5)


class AuditRead(ApiModel):
    audit_id: str
    case_id: str
    status: CaseStatus
    risk_score: int = 0
    confidence: float = 0
    summary: str
    invoice_total: float | None = None
    expected_total: float | None = None
    difference: float | None = None
    findings: list[dict[str, Any]] = Field(default_factory=list)
    discrepancies: list[dict[str, Any]] = Field(default_factory=list)
    top_reasons: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str | None = None
    documents: list[dict[str, Any]] = Field(default_factory=list)
    final_verdict: str | None = None
    created_at: datetime


class AuditHistoryResponse(ApiModel):
    history: list[AuditRead]


class AuditBatchResponse(ApiModel):
    audits: list[AuditRead]

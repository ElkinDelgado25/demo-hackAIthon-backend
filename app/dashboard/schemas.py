from datetime import datetime

from app.shared.schemas import ApiModel


class LatestAuditItem(ApiModel):
    audit_id: str
    case_id: str
    status: str
    created_at: datetime


class DashboardStatistics(ApiModel):
    total_cases: int = 0
    approved_cases: int = 0
    observed_cases: int = 0
    denied_cases: int = 0
    human_review_cases: int = 0
    approval_rate: int = 0
    latest_audits: list[LatestAuditItem] = []


class DenialReason(ApiModel):
    reason: str
    count: int
    percentage: int


class DenialReasonsResponse(ApiModel):
    reasons: list[DenialReason]

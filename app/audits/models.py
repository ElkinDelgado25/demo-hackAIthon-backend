from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field

from app.shared.enums import CaseStatus
from app.shared.schemas import utc_now


class Audit(Document):
    audit_id: str
    case_id: PydanticObjectId
    case_claim_number: str
    status: CaseStatus
    confidence: float = 0
    summary: str = "Dato no disponible"
    discrepancies: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str | None = None
    documents: list[dict[str, Any]] = Field(default_factory=list)
    executed_by: PydanticObjectId | None = None
    source: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "audits"

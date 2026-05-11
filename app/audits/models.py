from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field, field_validator

from app.shared.enums import CaseStatus
from app.shared.schemas import utc_now


class Audit(Document):
    audit_id: str = Field(default_factory=lambda: f"AUD-LEGACY")
    case_id: PydanticObjectId | str
    case_claim_number: str = ""
    status: CaseStatus = CaseStatus.OBSERVADO
    risk_score: int = 0
    confidence: float = 0
    summary: str = "Dato no disponible"
    invoice_total: float | None = None
    expected_total: float | None = None
    difference: float | None = None
    findings: list[dict[str, Any]] = Field(default_factory=list)
    discrepancies: list[dict[str, Any]] = Field(default_factory=list)
    top_reasons: list[str] = Field(default_factory=list)
    recommendation: str | None = None
    documents: list[dict[str, Any]] = Field(default_factory=list)
    final_verdict: str | None = None
    is_final: bool = False
    executed_by: PydanticObjectId | None = None
    source: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: Any) -> CaseStatus | Any:
        legacy_map = {
            "aprobado": CaseStatus.APROBADO,
            "rechazado": CaseStatus.DENEGADO,
            "observaciones": CaseStatus.OBSERVADO,
            "pendiente": CaseStatus.REVISION_HUMANA,
        }
        if isinstance(value, str):
            return legacy_map.get(value.lower(), value)
        return value

    class Settings:
        name = "audits"

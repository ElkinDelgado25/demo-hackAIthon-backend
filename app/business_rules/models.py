from datetime import datetime

from beanie import Document
from pydantic import Field

from app.shared.enums import RuleOperator, RuleStatus, RuleType, Severity
from app.shared.schemas import utc_now


class BusinessRule(Document):
    name: str
    description: str
    type: RuleType
    target_field: str
    operator: RuleOperator
    reference_value: str
    severity: Severity
    status: RuleStatus = RuleStatus.ACTIVA
    alert_message: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "business_rules"

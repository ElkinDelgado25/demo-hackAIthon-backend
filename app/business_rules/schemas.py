from datetime import datetime

from pydantic import Field

from app.shared.enums import RuleOperator, RuleStatus, RuleType, Severity
from app.shared.schemas import ApiModel


class BusinessRuleBase(ApiModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1)
    type: RuleType
    target_field: str = Field(min_length=1, max_length=160)
    operator: RuleOperator
    reference_value: str = Field(min_length=1, max_length=240)
    severity: Severity
    status: RuleStatus = RuleStatus.ACTIVA
    alert_message: str = Field(min_length=1)


class BusinessRuleCreate(BusinessRuleBase):
    pass


class BusinessRuleUpdate(BusinessRuleBase):
    pass


class BusinessRuleRead(BusinessRuleBase):
    id: str
    created_at: datetime
    updated_at: datetime


class BusinessRuleListResponse(ApiModel):
    rules: list[BusinessRuleRead]

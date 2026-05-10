from app.business_rules.models import BusinessRule
from app.business_rules.schemas import BusinessRuleCreate, BusinessRuleRead, BusinessRuleUpdate
from app.core.exceptions import NotFoundError
from app.shared.enums import RuleStatus
from app.shared.schemas import public_id, utc_now


def rule_to_read(rule: BusinessRule) -> BusinessRuleRead:
    return BusinessRuleRead(
        id=public_id(rule.id),
        name=rule.name,
        description=rule.description,
        type=rule.type,
        target_field=rule.target_field,
        operator=rule.operator,
        reference_value=rule.reference_value,
        severity=rule.severity,
        status=rule.status,
        alert_message=rule.alert_message,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


async def list_rules() -> list[BusinessRuleRead]:
    rules = await BusinessRule.find_all().sort("-updated_at").to_list()
    return [rule_to_read(item) for item in rules]


async def create_rule(payload: BusinessRuleCreate) -> BusinessRuleRead:
    rule = BusinessRule(**payload.model_dump())
    await rule.insert()
    return rule_to_read(rule)


async def get_rule_or_404(rule_id: str) -> BusinessRule:
    try:
        rule = await BusinessRule.get(rule_id)
    except Exception:
        rule = None
    if not rule:
        raise NotFoundError("Regla de negocio no encontrada.")
    return rule


async def update_rule(rule_id: str, payload: BusinessRuleUpdate) -> BusinessRuleRead:
    rule = await get_rule_or_404(rule_id)
    data = payload.model_dump()
    for field, value in data.items():
        setattr(rule, field, value)
    rule.updated_at = utc_now()
    await rule.save()
    return rule_to_read(rule)


async def toggle_rule(rule_id: str) -> BusinessRuleRead:
    rule = await get_rule_or_404(rule_id)
    rule.status = RuleStatus.INACTIVA if rule.status == RuleStatus.ACTIVA else RuleStatus.ACTIVA
    rule.updated_at = utc_now()
    await rule.save()
    return rule_to_read(rule)


async def delete_rule(rule_id: str) -> None:
    rule = await get_rule_or_404(rule_id)
    await rule.delete()

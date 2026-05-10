from fastapi import APIRouter, Depends, Response

from app.business_rules.schemas import BusinessRuleCreate, BusinessRuleListResponse, BusinessRuleRead, BusinessRuleUpdate
from app.business_rules.service import create_rule, delete_rule, list_rules, toggle_rule, update_rule
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/business-rules", tags=["business-rules"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=BusinessRuleListResponse)
async def get_business_rules() -> BusinessRuleListResponse:
    return BusinessRuleListResponse(rules=await list_rules())


@router.post("", response_model=BusinessRuleRead, status_code=201)
async def post_business_rule(payload: BusinessRuleCreate) -> BusinessRuleRead:
    return await create_rule(payload)


@router.put("/{rule_id}", response_model=BusinessRuleRead)
async def put_business_rule(rule_id: str, payload: BusinessRuleUpdate) -> BusinessRuleRead:
    return await update_rule(rule_id, payload)


@router.patch("/{rule_id}/toggle", response_model=BusinessRuleRead)
async def patch_business_rule_toggle(rule_id: str) -> BusinessRuleRead:
    return await toggle_rule(rule_id)


@router.delete("/{rule_id}", status_code=204)
async def delete_business_rule(rule_id: str) -> Response:
    await delete_rule(rule_id)
    return Response(status_code=204)

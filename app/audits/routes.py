from fastapi import APIRouter, Depends

from app.audits.schemas import AuditHistoryResponse, AuditRead, AuditRunRequest
from app.audits.service import get_audit_history, get_latest_audit, run_audit
from app.core.dependencies import CurrentUser, get_current_user

router = APIRouter(prefix="/audit", tags=["audits"], dependencies=[Depends(get_current_user)])


@router.post("/{case_id}", response_model=AuditRead)
async def post_audit(case_id: str, payload: AuditRunRequest, current_user: CurrentUser) -> AuditRead:
    return await run_audit(case_id, payload, current_user)


@router.get("/{case_id}/latest", response_model=AuditRead)
async def latest_audit(case_id: str) -> AuditRead:
    return await get_latest_audit(case_id)


@router.get("/{case_id}/history", response_model=AuditHistoryResponse)
async def audit_history(case_id: str) -> AuditHistoryResponse:
    return AuditHistoryResponse(history=await get_audit_history(case_id))

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.dashboard.schemas import DashboardStatistics, DenialReasonsResponse
from app.dashboard.service import get_dashboard_statistics, get_denial_reasons

router = APIRouter(prefix="/statistics", tags=["statistics"], dependencies=[Depends(get_current_user)])


@router.get("/dashboard", response_model=DashboardStatistics)
async def dashboard_statistics() -> DashboardStatistics:
    return await get_dashboard_statistics()


@router.get("/denial-reasons", response_model=DenialReasonsResponse)
async def denial_reasons() -> DenialReasonsResponse:
    return DenialReasonsResponse(reasons=await get_denial_reasons())

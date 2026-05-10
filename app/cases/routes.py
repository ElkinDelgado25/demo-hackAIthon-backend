from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.cases.schemas import CaseCreate, CaseListResponse, CaseRead, CaseStatusUpdate, DocumentsResponse
from app.cases.service import create_case, get_case, list_cases, list_documents, update_case_status, upload_documents
from app.core.dependencies import CurrentUser, get_current_user

router = APIRouter(prefix="/cases", tags=["cases"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=CaseListResponse)
async def get_cases() -> CaseListResponse:
    return CaseListResponse(cases=await list_cases())


@router.post("", response_model=CaseRead, status_code=201)
async def post_case(payload: CaseCreate) -> CaseRead:
    return await create_case(payload)


@router.get("/{case_id}", response_model=CaseRead)
async def get_case_by_id(case_id: str) -> CaseRead:
    return await get_case(case_id)


@router.patch("/{case_id}/status", response_model=CaseRead)
async def patch_case_status(case_id: str, payload: CaseStatusUpdate) -> CaseRead:
    return await update_case_status(case_id, payload.status)


@router.get("/{case_id}/documents", response_model=DocumentsResponse)
async def get_case_documents(case_id: str) -> DocumentsResponse:
    return DocumentsResponse(documents=await list_documents(case_id))


@router.post("/{case_id}/documents", response_model=DocumentsResponse, status_code=201)
async def post_case_documents(
    case_id: str,
    current_user: CurrentUser,
    files: Annotated[list[UploadFile], File()],
    documents: Annotated[str, Form()],
) -> DocumentsResponse:
    return DocumentsResponse(documents=await upload_documents(case_id, files, documents, current_user))

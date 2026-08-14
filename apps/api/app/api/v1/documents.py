import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.schemas.risk_analysis import RiskAnalysisResponse
from app.services.document_service import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    process_document,
)
from app.services.risk_analysis_service import analyze_document, get_latest_analysis, start_analysis

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    document = await create_document(
        db,
        organization_id=current_user.organization_id,
        owner_id=current_user.id,
        filename=file.filename or "untitled",
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    background_tasks.add_task(process_document, document.id)
    return document


@router.get("", response_model=DocumentListResponse)
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    documents = await list_documents(db, current_user.organization_id)
    return DocumentListResponse(documents=documents)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_document(db, document_id, current_user.organization_id)


@router.delete("/{document_id}", status_code=204)
async def delete_document_by_id(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_document(db, document_id, current_user.organization_id)


@router.post("/{document_id}/analyze", response_model=RiskAnalysisResponse)
async def analyze_document_by_id(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Confirms the document exists, belongs to this org, and is fully
    # indexed before queuing analysis against it.
    document = await get_document(db, document_id, current_user.organization_id)
    analysis = await start_analysis(db, document.id, current_user.organization_id)
    background_tasks.add_task(analyze_document, document.id, current_user.organization_id)
    return analysis


@router.get("/{document_id}/analysis", response_model=RiskAnalysisResponse)
async def get_document_analysis(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_latest_analysis(db, document_id, current_user.organization_id)

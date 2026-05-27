from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.schemas.document import DocumentExtractResponse
from app.services import document_service

router = APIRouter()


@router.post("/extract", response_model=DocumentExtractResponse)
async def extract_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await document_service.extract_from_pdf(file)

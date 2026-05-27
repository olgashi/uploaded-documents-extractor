from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.core.limiter import limiter
from app.schemas.auth import UserResponse
from app.schemas.document import DocumentExtractResponse
from app.services import document_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/extract", response_model=DocumentExtractResponse)
@limiter.limit(settings.RATE_LIMIT_EXTRACT)
async def extract_document(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await document_service.extract_from_pdf(file)

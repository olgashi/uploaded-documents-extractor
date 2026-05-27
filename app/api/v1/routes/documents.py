from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.schemas.document import DocumentExtractResponse
from app.schemas.order import OrderCreate, OrderResponse
from app.services import document_service, order_service

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


@router.post(
    "/upload-order",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.RATE_LIMIT_EXTRACT)
async def upload_document_order(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    result = await document_service.extract_from_pdf(file)
    payload = OrderCreate(
        patient_first_name=result.extraction.first_name,
        patient_last_name=result.extraction.last_name,
        patient_dob=result.extraction.date_of_birth,
        document_filename=result.filename,
    )
    existing = await order_service.get_uploaded_duplicate(db, current_user.id, payload)
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return existing

    return await order_service.create_order(
        db,
        current_user.id,
        payload,
    )

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse, OrderUpdate
from app.services import order_service

router = APIRouter()


@router.get("", response_model=OrderListResponse)
@cache(expire=30)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    items, total = await order_service.list_orders(db, current_user.id, page, page_size)
    return OrderListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await order_service.create_order(db, current_user.id, payload)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await order_service.get_order(db, order_id)


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    payload: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await order_service.update_order(db, order_id, payload)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    await order_service.delete_order(db, order_id)

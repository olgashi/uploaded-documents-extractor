import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.repositories import order_repo
from app.schemas.order import OrderCreate, OrderUpdate


async def create_order(db: AsyncSession, user_id: uuid.UUID, payload: OrderCreate) -> Order:
    return await order_repo.create(db, user_id, payload)


async def get_order(db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    order = await order_repo.get_by_id(db, order_id, user_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


async def list_orders(
    db: AsyncSession, user_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[Order], int]:
    return await order_repo.get_all(db, user_id, page, page_size)


async def update_order(
    db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID, payload: OrderUpdate
) -> Order:
    order = await order_repo.get_by_id(db, order_id, user_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return await order_repo.update(db, order, payload)


async def delete_order(db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> None:
    order = await order_repo.get_by_id(db, order_id, user_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    await order_repo.delete(db, order)

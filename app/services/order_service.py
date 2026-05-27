import uuid

from fastapi import HTTPException, status
from fastapi_cache import FastAPICache
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.repositories import order_repo
from app.schemas.order import OrderCreate, OrderUpdate


async def create_order(db: AsyncSession, user_id: uuid.UUID, payload: OrderCreate) -> Order:
    order = await order_repo.create(db, user_id, payload)
    await FastAPICache.clear()
    return order


async def get_order(db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    order = await order_repo.get_by_id(db, order_id, user_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


async def list_orders(
    db: AsyncSession, user_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[Order], int]:
    return await order_repo.get_all(db, user_id, page, page_size)


async def get_uploaded_duplicate(
    db: AsyncSession, user_id: uuid.UUID, payload: OrderCreate
) -> Order | None:
    return await order_repo.get_uploaded_duplicate(db, user_id, payload)


async def update_order(
    db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID, payload: OrderUpdate
) -> Order:
    order = await order_repo.get_by_id(db, order_id, user_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    updated = await order_repo.update(db, order, payload)
    await FastAPICache.clear()
    return updated


async def delete_order(db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> None:
    order = await order_repo.get_by_id(db, order_id, user_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    await order_repo.delete(db, order)
    await FastAPICache.clear()


async def delete_user_orders(db: AsyncSession, user_id: uuid.UUID) -> int:
    deleted = await order_repo.delete_all_by_user(db, user_id)
    await FastAPICache.clear()
    return deleted

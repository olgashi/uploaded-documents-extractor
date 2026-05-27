import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.schemas.order import OrderCreate, OrderUpdate


async def create(db: AsyncSession, user_id: uuid.UUID, payload: OrderCreate) -> Order:
    order = Order(
        patient_first_name=payload.patient_first_name,
        patient_last_name=payload.patient_last_name,
        patient_dob=payload.patient_dob,
        document_filename=payload.document_filename,
        notes=payload.notes,
        created_by=user_id,
    )
    db.add(order)
    await db.flush()
    return order


async def get_by_id(
    db: AsyncSession, order_id: uuid.UUID, user_id: uuid.UUID | None = None
) -> Order | None:
    query = select(Order).where(Order.id == order_id)
    if user_id is not None:
        query = query.where(Order.created_by == user_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_all(
    db: AsyncSession, user_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[Order], int]:
    base = select(Order).where(Order.created_by == user_id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    items = list(
        (
            await db.execute(
                base.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
            )
        ).scalars().all()
    )
    return items, total


async def update(db: AsyncSession, order: Order, payload: OrderUpdate) -> Order:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, key, value)
    await db.flush()
    return order


async def delete(db: AsyncSession, order: Order) -> None:
    await db.delete(order)
    await db.flush()

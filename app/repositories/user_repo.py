import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create(
    db: AsyncSession, email: str, hashed_password: str, is_admin: bool = False
) -> User:
    user = User(email=email, hashed_password=hashed_password, is_admin=is_admin)
    db.add(user)
    await db.flush()
    return user

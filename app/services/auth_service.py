import structlog
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.user import User
from app.repositories import user_repo

logger = structlog.get_logger(__name__)


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    user = await user_repo.get_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def seed_admin() -> None:
    """Create the admin user on first startup if the table is empty."""
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        existing = await user_repo.get_by_email(db, settings.ADMIN_EMAIL)
        if existing:
            return
        await user_repo.create(
            db,
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            is_admin=True,
        )
        await db.commit()
        logger.info("admin_seeded", email=settings.ADMIN_EMAIL)

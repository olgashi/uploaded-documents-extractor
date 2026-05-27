import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.repositories import user_repo
from app.schemas.auth import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise _UNAUTH
    except JWTError:
        raise _UNAUTH

    try:
        parsed_user_id = uuid.UUID(user_id)
    except (AttributeError, TypeError, ValueError):
        raise _UNAUTH

    user = await user_repo.get_by_id(db, parsed_user_id)
    if user is None or not user.is_active:
        raise _UNAUTH

    request.state.current_user_id = user.id
    return UserResponse.model_validate(user)

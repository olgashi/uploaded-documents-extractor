"""
Shared pytest fixtures.

Test DB runs on port 5433 (db_test service in compose.yml) so tests
never touch the dev database.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.schemas.auth import UserResponse

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5433/documents_test_db"
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def fake_user() -> UserResponse:
    return UserResponse(
        id=uuid.uuid4(),
        email="test@example.com",
        is_active=True,
        is_admin=False,
    )


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Unauthenticated client — use for login and public endpoint tests."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authed_client(db_session: AsyncSession, fake_user: UserResponse) -> AsyncClient:
    """Client with get_current_user bypassed — use for all protected endpoint tests."""
    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return fake_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

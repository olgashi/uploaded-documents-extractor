"""
Shared pytest fixtures.

Test DB runs on port 5433 (db_test service in compose.yml) so tests
never touch the dev database.

DATABASE_URL is overridden in os.environ before app imports so that AsyncSessionLocal
(used by the activity-log middleware) also targets the test DB. This lets middleware
commits be visible to the test's db_session via READ COMMITTED.

Event-loop note: asyncpg_default_fixture_loop_scope = "function" ensures function-scoped
async fixtures run on the same event loop as the test.
"""

import asyncio
import os
import uuid

# Must be set before any app imports so settings/engine are initialized with the test DB.
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/documents_test_db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from fastapi import Request  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.core.security import get_current_user  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas.auth import UserResponse  # noqa: E402

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5433/documents_test_db"
)


@pytest.fixture(scope="session")
def create_tables():
    """Run DDL once per session using asyncio.run() to stay loop-independent."""
    async def _ddl(drop: bool) -> None:
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            if drop:
                await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_ddl(drop=True))
    yield
    asyncio.run(_ddl(drop=False))  # leave tables; DB is wiped on next test run


@pytest_asyncio.fixture
async def db_session(create_tables) -> AsyncSession:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    try:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            yield session
            await session.rollback()
    finally:
        await engine.dispose()


@pytest.fixture
def fake_user() -> UserResponse:
    return UserResponse(
        id=uuid.uuid4(),
        email="test@example.com",
        is_active=True,
        is_admin=False,
    )


@pytest_asyncio.fixture
async def db_user(db_session: AsyncSession) -> UserResponse:
    """A real persisted user for auth integration tests."""
    from app.repositories.user_repo import create
    from app.services.auth_service import hash_password

    user = await create(
        db_session,
        email="test@example.com",
        hashed_password=hash_password("test-password-123"),
    )
    await db_session.flush()
    return UserResponse.model_validate(user)


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
async def db_fake_user(db_session: AsyncSession, fake_user: UserResponse) -> UserResponse:
    """Stage fake_user in the session so FK constraints on orders.created_by are satisfied.
    No explicit flush — SQLAlchemy inserts the user before the first order (UoW FK ordering)."""
    from app.db.models.user import User

    db_session.add(User(
        id=fake_user.id,
        email=fake_user.email,
        hashed_password="test-hash",
        is_active=True,
        is_admin=False,
    ))
    return fake_user


@pytest_asyncio.fixture
async def authed_client(db_session: AsyncSession, db_fake_user: UserResponse) -> AsyncClient:
    """Client with get_current_user bypassed — use for all protected endpoint tests."""
    async def override_get_db():
        yield db_session

    async def override_get_current_user(request: Request):
        request.state.current_user_id = db_fake_user.id
        return db_fake_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

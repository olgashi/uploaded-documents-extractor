"""Activity logging tests — will fail until middleware is implemented."""

import pytest
from sqlalchemy import select

from app.db.models.activity_log import ActivityLog


@pytest.mark.integration
async def test_activity_logged_on_health_check(client, db_session):
    await client.get("/api/v1/health")
    result = await db_session.execute(
        select(ActivityLog).where(ActivityLog.path == "/api/v1/health")
    )
    log = result.scalars().first()
    assert log is not None
    assert log.method == "GET"
    assert log.status_code == 200
    assert log.duration_ms >= 0


@pytest.mark.integration
async def test_activity_log_captures_user_id(authed_client, db_session, fake_user):
    await authed_client.get("/api/v1/orders")
    result = await db_session.execute(
        select(ActivityLog).where(ActivityLog.path == "/api/v1/orders")
    )
    log = result.scalars().first()
    assert log is not None
    assert log.user_id == fake_user.id


@pytest.mark.integration
async def test_activity_log_null_user_for_unauthenticated(client, db_session):
    await client.post(
        "/api/v1/auth/token",
        data={"username": "x@x.com", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    result = await db_session.execute(
        select(ActivityLog).where(ActivityLog.path == "/api/v1/auth/token")
    )
    log = result.scalars().first()
    assert log is not None
    assert log.user_id is None


@pytest.mark.integration
async def test_activity_log_captures_ip(client, db_session):
    await client.get("/api/v1/health")
    result = await db_session.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc())
    )
    log = result.scalars().first()
    assert log is not None
    assert log.ip_address


@pytest.mark.integration
async def test_activity_log_captures_request_id(client, db_session):
    await client.get("/api/v1/health")
    result = await db_session.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc())
    )
    log = result.scalars().first()
    assert log is not None
    assert log.request_id

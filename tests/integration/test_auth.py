"""
Auth route tests — authenticate() is mocked so no DB connection is needed.
This keeps auth tests fast and decoupled from the DB layer.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from jose import jwt

from app.core.config import settings
from app.db.models.user import User

_PATCH = "app.api.v1.routes.auth.authenticate"


def _fake_db_user(email: str = "test@example.com") -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        hashed_password="irrelevant",
        is_active=True,
        is_admin=False,
    )


@pytest.mark.integration
async def test_login_returns_token(client):
    fake = _fake_db_user()
    with patch(_PATCH, new=AsyncMock(return_value=fake)):
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": fake.email, "password": "any"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.integration
async def test_login_token_encodes_user_id(client):
    fake = _fake_db_user()
    with patch(_PATCH, new=AsyncMock(return_value=fake)):
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": fake.email, "password": "any"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    payload = jwt.decode(
        resp.json()["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert payload["sub"] == str(fake.id)


@pytest.mark.integration
async def test_login_wrong_password_returns_401(client):
    with patch(_PATCH, new=AsyncMock(return_value=None)):
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "test@example.com", "password": "wrong"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert resp.status_code == 401


@pytest.mark.integration
async def test_login_unknown_email_returns_401(client):
    with patch(_PATCH, new=AsyncMock(return_value=None)):
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "nobody@example.com", "password": "x"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert resp.status_code == 401


@pytest.mark.integration
async def test_protected_route_without_token_returns_401(client):
    resp = await client.get("/api/v1/orders")
    assert resp.status_code == 401


@pytest.mark.integration
async def test_protected_route_with_invalid_token_returns_401(client):
    resp = await client.get(
        "/api/v1/orders", headers={"Authorization": "Bearer not.a.valid.token"}
    )
    assert resp.status_code == 401

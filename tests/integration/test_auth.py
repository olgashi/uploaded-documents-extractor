"""Auth endpoint tests — will fail (501) until auth service is implemented."""

import pytest


@pytest.mark.integration
async def test_login_returns_token(client):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "changeme-secure-12345"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.integration
async def test_login_wrong_password_returns_401(client):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "wrong-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


@pytest.mark.integration
async def test_login_unknown_email_returns_401(client):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "nobody@example.com", "password": "irrelevant"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


@pytest.mark.integration
async def test_protected_route_without_token_returns_401(client):
    response = await client.get("/api/v1/orders")
    assert response.status_code == 401


@pytest.mark.integration
async def test_protected_route_with_invalid_token_returns_401(client):
    response = await client.get(
        "/api/v1/orders",
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert response.status_code == 401

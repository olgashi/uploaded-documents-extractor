"""Health check — implemented, should pass immediately."""

import pytest


@pytest.mark.integration
async def test_health_returns_ok(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


@pytest.mark.integration
async def test_health_requires_no_auth(client):
    """Health endpoint must be publicly accessible — used by load balancer probes."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.integration
async def test_api_responses_include_security_headers(client):
    response = await client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"

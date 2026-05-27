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

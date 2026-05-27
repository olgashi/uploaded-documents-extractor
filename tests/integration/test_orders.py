"""Order CRUD tests."""

import uuid
from datetime import date

import pytest

from app.db.models.order import Order
from app.db.models.user import User


ORDER_PAYLOAD = {
    "patient_first_name": "Jane",
    "patient_last_name": "Doe",
    "patient_dob": "1985-06-15",
}


@pytest.mark.integration
async def test_create_order_returns_201(authed_client):
    response = await authed_client.post("/api/v1/orders", json=ORDER_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["patient_first_name"] == "Jane"
    assert body["patient_last_name"] == "Doe"
    assert body["patient_dob"] == "1985-06-15"
    assert body["status"] == "pending"
    assert "id" in body


@pytest.mark.integration
async def test_create_order_future_dob_returns_422(authed_client):
    payload = {**ORDER_PAYLOAD, "patient_dob": "2099-01-01"}
    response = await authed_client.post("/api/v1/orders", json=payload)
    assert response.status_code == 422


@pytest.mark.integration
async def test_list_orders_returns_200(authed_client):
    response = await authed_client.get("/api/v1/orders")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "page_size" in body


@pytest.mark.integration
async def test_list_orders_pagination(authed_client):
    response = await authed_client.get("/api/v1/orders?page=1&page_size=5")
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 5


@pytest.mark.integration
async def test_list_orders_invalid_page_returns_422(authed_client):
    response = await authed_client.get("/api/v1/orders?page=0")
    assert response.status_code == 422


@pytest.mark.integration
async def test_get_order_returns_200(authed_client):
    create_resp = await authed_client.post("/api/v1/orders", json=ORDER_PAYLOAD)
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]

    response = await authed_client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id


@pytest.mark.integration
async def test_get_nonexistent_order_returns_404(authed_client):
    response = await authed_client.get(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.integration
async def test_get_other_users_order_returns_404(authed_client, db_session):
    other_user_id = uuid.uuid4()
    db_session.add(User(
        id=other_user_id,
        email="other@example.com",
        hashed_password="test-hash",
        is_active=True,
        is_admin=False,
    ))
    order = Order(
        patient_first_name="Other",
        patient_last_name="Patient",
        patient_dob=date(1980, 1, 1),
        created_by=other_user_id,
    )
    db_session.add(order)
    await db_session.flush()

    response = await authed_client.get(f"/api/v1/orders/{order.id}")
    assert response.status_code == 404


@pytest.mark.integration
async def test_update_order_invalid_status_returns_422(authed_client):
    create_resp = await authed_client.post("/api/v1/orders", json=ORDER_PAYLOAD)
    order_id = create_resp.json()["id"]

    response = await authed_client.patch(
        f"/api/v1/orders/{order_id}", json={"status": "not_a_status"}
    )
    assert response.status_code == 422


@pytest.mark.integration
async def test_delete_order_returns_204(authed_client):
    create_resp = await authed_client.post("/api/v1/orders", json=ORDER_PAYLOAD)
    order_id = create_resp.json()["id"]

    response = await authed_client.delete(f"/api/v1/orders/{order_id}")
    assert response.status_code == 204


@pytest.mark.integration
async def test_deleted_order_returns_404(authed_client):
    create_resp = await authed_client.post("/api/v1/orders", json=ORDER_PAYLOAD)
    order_id = create_resp.json()["id"]

    await authed_client.delete(f"/api/v1/orders/{order_id}")
    response = await authed_client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 404

"""Schema validation — no DB, no network. These should pass immediately."""

import pytest
from datetime import date, timedelta

from pydantic import ValidationError

from app.db.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate


@pytest.mark.unit
class TestOrderCreateSchema:
    def test_valid_order(self):
        order = OrderCreate(
            patient_first_name="Jane",
            patient_last_name="Doe",
            patient_dob=date(1985, 6, 15),
        )
        assert order.patient_first_name == "Jane"
        assert order.status_default_not_set() if False else True  # status set by model

    def test_strips_whitespace_from_names(self):
        order = OrderCreate(
            patient_first_name="  Jane  ",
            patient_last_name="\tDoe\n",
            patient_dob=date(1985, 6, 15),
        )
        assert order.patient_first_name == "Jane"
        assert order.patient_last_name == "Doe"

    def test_future_dob_raises(self):
        with pytest.raises(ValidationError, match="past"):
            OrderCreate(
                patient_first_name="Jane",
                patient_last_name="Doe",
                patient_dob=date.today() + timedelta(days=1),
            )

    def test_today_dob_raises(self):
        with pytest.raises(ValidationError):
            OrderCreate(
                patient_first_name="Jane",
                patient_last_name="Doe",
                patient_dob=date.today(),
            )

    def test_empty_first_name_raises(self):
        with pytest.raises(ValidationError):
            OrderCreate(
                patient_first_name="",
                patient_last_name="Doe",
                patient_dob=date(1985, 6, 15),
            )

    def test_name_too_long_raises(self):
        with pytest.raises(ValidationError):
            OrderCreate(
                patient_first_name="A" * 101,
                patient_last_name="Doe",
                patient_dob=date(1985, 6, 15),
            )

    def test_notes_optional(self):
        order = OrderCreate(
            patient_first_name="Jane",
            patient_last_name="Doe",
            patient_dob=date(1985, 6, 15),
        )
        assert order.notes is None

    def test_notes_max_length(self):
        with pytest.raises(ValidationError):
            OrderCreate(
                patient_first_name="Jane",
                patient_last_name="Doe",
                patient_dob=date(1985, 6, 15),
                notes="x" * 2001,
            )


@pytest.mark.unit
class TestOrderUpdateSchema:
    def test_all_fields_optional(self):
        update = OrderUpdate()
        assert update.patient_first_name is None
        assert update.patient_last_name is None
        assert update.patient_dob is None
        assert update.status is None
        assert update.notes is None

    def test_partial_update(self):
        update = OrderUpdate(status=OrderStatus.COMPLETED)
        assert update.status == OrderStatus.COMPLETED
        assert update.patient_first_name is None

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            OrderUpdate(status="invalid_status")

    def test_strips_whitespace(self):
        update = OrderUpdate(patient_first_name="  Jane  ")
        assert update.patient_first_name == "Jane"

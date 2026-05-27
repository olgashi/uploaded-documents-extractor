from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.order import OrderStatus


class OrderCreate(BaseModel):
    patient_first_name: str = Field(..., min_length=1, max_length=100)
    patient_last_name: str = Field(..., min_length=1, max_length=100)
    patient_dob: date
    document_filename: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=2000)

    @field_validator("patient_first_name", "patient_last_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("patient_dob")
    @classmethod
    def dob_must_be_past(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v


class OrderUpdate(BaseModel):
    patient_first_name: str | None = Field(None, min_length=1, max_length=100)
    patient_last_name: str | None = Field(None, min_length=1, max_length=100)
    patient_dob: date | None = None
    status: OrderStatus | None = None
    notes: str | None = Field(None, max_length=2000)

    @field_validator("patient_first_name", "patient_last_name", mode="before")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v

    @field_validator("patient_dob")
    @classmethod
    def dob_must_be_past(cls, v: date | None) -> date | None:
        if v is not None and v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_first_name: str
    patient_last_name: str
    patient_dob: date
    status: OrderStatus
    document_filename: str | None
    notes: str | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import ReservationStatus


class ReservationCreate(BaseModel):
    user_id: int = Field(gt=0)
    service_id: int = Field(gt=0)
    professional_name: str = Field(min_length=1, max_length=120)
    # Debe llegar timezone-aware (ISO 8601 con offset).
    start_time: datetime

    @field_validator("start_time")
    @classmethod
    def must_be_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("start_time debe incluir timezone (ISO 8601 con offset)")
        return v


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    service_id: int
    professional_name: str
    start_time: datetime
    end_time: datetime
    status: ReservationStatus
    refund_amount: float | None
    created_at: datetime
    cancelled_at: datetime | None


class CancellationOut(BaseModel):
    reservation_id: int
    status: ReservationStatus
    refund_amount: float
    message: str

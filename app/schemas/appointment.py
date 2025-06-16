from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.schemas.validators import validate_phone


class AppointmentCreate(BaseModel):
    barber_id: int
    schedule_id: int
    client_name: Optional[str] = None
    client_phone: Optional[str] = None

    @field_validator("client_phone")
    def phone_valid(cls, v):
        return validate_phone(v)


class AppointmentOut(BaseModel):
    id: int
    barber_id: int
    client_name: str
    client_phone: str
    appointment_time: datetime
    status: str

    class Config:
        from_attributes = True

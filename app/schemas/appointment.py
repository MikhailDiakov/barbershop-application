from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    client_name: Optional[str]
    client_phone: str
    barber_id: int
    appointment_time: datetime


class AppointmentOut(BaseModel):
    id: int
    client_name: Optional[str]
    client_phone: str
    barber_id: int
    appointment_time: datetime
    status: str

    class Config:
        orm_mode = True

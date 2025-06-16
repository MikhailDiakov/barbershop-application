from datetime import date, time

from pydantic import BaseModel


class BarberScheduleBase(BaseModel):
    date: date
    start_time: time
    end_time: time
    is_active: bool = True

    class Config:
        from_attributes = True
        json_encoders = {time: lambda v: v.strftime("%H:%M")}


class BarberScheduleCreate(BarberScheduleBase):
    pass


class BarberScheduleUpdate(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None


class BarberScheduleOut(BarberScheduleBase):
    id: int

    class Config:
        from_attributes = True

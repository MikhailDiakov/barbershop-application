import datetime

from pydantic import BaseModel


class BarberScheduleBase(BaseModel):
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    is_active: bool = True

    class Config:
        from_attributes = True
        json_encoders = {datetime.time: lambda v: v.strftime("%H:%M")}


class BarberScheduleCreate(BarberScheduleBase):
    pass


class BarberScheduleUpdate(BaseModel):
    date: datetime.date | None = None
    start_time: datetime.time | None = None
    end_time: datetime.time | None = None
    is_active: bool | None = None


class BarberScheduleOut(BarberScheduleBase):
    id: int

    class Config:
        from_attributes = True


class ScheduleOut(BaseModel):
    id: int
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time

    class Config:
        from_attributes = True
        json_encoders = {datetime.time: lambda v: v.strftime("%H:%M")}


class BarberWithScheduleOut(BaseModel):
    id: int
    full_name: str
    avatar_url: str | None
    schedules: list[ScheduleOut]

    class Config:
        from_attributes = True


class AdminBarberScheduleCreate(BarberScheduleBase):
    barber_id: int


class AdminBarberScheduleUpdate(BarberScheduleUpdate):
    date: datetime.date | None = None
    barber_id: int | None = None


class AdminBarberScheduleOut(BarberScheduleOut):
    barber_id: int

    class Config:
        from_attributes = True

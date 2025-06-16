from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_current_user_optional, get_session
from app.schemas.appointment import AppointmentCreate, AppointmentOut
from app.schemas.barber_schedule import BarberWithScheduleOut
from app.services.booking_service import (
    create_appointment_service,
    get_appointments_by_user,
)
from app.utils.selectors.schedule import get_barbers_with_schedules

router = APIRouter()


@router.get("/available-slots", response_model=list[BarberWithScheduleOut])
async def get_barbers_with_available_slots(db: AsyncSession = Depends(get_session)):
    barbers = await get_barbers_with_schedules(db)
    return barbers


@router.post("/", response_model=AppointmentOut)
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_optional),
):
    appointment = await create_appointment_service(db, data, current_user)
    return appointment


@router.get("/my", response_model=list[AppointmentOut])
async def get_my_appointments(
    upcoming_only: Optional[bool] = Query(
        False, description="If True, return only upcoming appointments"
    ),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    user_id = current_user["id"]
    appointments = await get_appointments_by_user(db, user_id, upcoming_only)
    return appointments

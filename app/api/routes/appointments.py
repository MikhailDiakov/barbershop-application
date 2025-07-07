from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_current_user_optional, get_session
from app.schemas.appointment import AppointmentCreate, AppointmentOut
from app.schemas.barber import BarberOutwithReviews, BarberOutwithReviewsDetailed
from app.schemas.barber_schedule import BarberWithScheduleAndReviewsOut
from app.services.appointment_service import (
    create_appointment_service,
    get_appointments_by_user,
    get_barber_detailed_info,
    get_barbers_with_ratings,
    get_barbers_with_schedules_and_ratings,
)

router = APIRouter()


@router.get("/barbers", response_model=List[BarberOutwithReviews])
async def list_barbers(db: AsyncSession = Depends(get_session)):
    return await get_barbers_with_ratings(db)


@router.get("/barbers/{barber_id}", response_model=BarberOutwithReviewsDetailed)
async def get_barber_details(barber_id: int, db: AsyncSession = Depends(get_session)):
    return await get_barber_detailed_info(db, barber_id)


@router.get("/available-slots", response_model=list[BarberWithScheduleAndReviewsOut])
async def get_barbers_with_available_slots(db: AsyncSession = Depends(get_session)):
    return await get_barbers_with_schedules_and_ratings(db)


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

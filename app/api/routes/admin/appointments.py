from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_session
from app.schemas.appointment import AppointmentCreate, AppointmentOut
from app.services.admin.appointment import (
    admin_create_appointment_service,
    admin_delete_appointment_service,
    admin_get_appointments_service,
)

router = APIRouter()


@router.get("/", response_model=list[AppointmentOut])
async def admin_get_appointments_route(
    upcoming_only: bool = Query(True, description="Only future appointments"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await admin_get_appointments_service(
        db,
        upcoming_only,
        skip,
        limit,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.post("/", response_model=AppointmentOut)
async def admin_create_appointment_route(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await admin_create_appointment_service(
        db,
        data,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_appointment_route(
    appointment_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await admin_delete_appointment_service(
        db,
        appointment_id,
        current_user["role"],
        admin_id=current_user["id"],
    )

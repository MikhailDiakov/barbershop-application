from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_session
from app.schemas.barber import BarberCreate, BarberOut, BarberUpdate
from app.schemas.barber_schedule import (
    AdminBarberScheduleCreate,
    AdminBarberScheduleOut,
    AdminBarberScheduleUpdate,
)
from app.services.admin.barbers import (
    admin_create_schedule_service,
    admin_delete_schedule_service,
    admin_get_all_schedules,
    admin_update_schedule_service,
    create_barber,
    delete_barber,
    get_all_barbers,
    get_barber_by_id,
    remove_barber_photo,
    update_barber_by_admin,
    upload_barber_photo,
)

router = APIRouter()


@router.get("/", response_model=list[BarberOut])
async def list_barbers(
    db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user_info)
):
    return await get_all_barbers(
        db,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.get("/{barber_id}", response_model=BarberOut)
async def get_barber(
    barber_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_barber_by_id(
        db,
        barber_id,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.post("/create", response_model=BarberOut, status_code=status.HTTP_201_CREATED)
async def add_barber(
    barber: BarberCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await create_barber(
        db,
        barber,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.put("/{barber_id}", response_model=BarberOut)
async def update_barber(
    barber_id: int,
    data: BarberUpdate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await update_barber_by_admin(
        db=db,
        barber_id=barber_id,
        data=data,
        user_role=current_user["role"],
        admin_id=current_user["id"],
    )


@router.delete("/{barber_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_barber(
    barber_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await delete_barber(
        db,
        barber_id,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.post("/{barber_id}/avatar", response_model=BarberOut)
async def upload_barber_avatar(
    barber_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await upload_barber_photo(
        db,
        barber_id,
        file,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.delete("/{barber_id}/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_barber_avatar(
    barber_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await remove_barber_photo(
        db,
        barber_id,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.get("/schedules/", response_model=list[AdminBarberScheduleOut])
async def admin_list_schedules(
    upcoming_only: bool = Query(default=False),
    barber_id: Optional[int] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await admin_get_all_schedules(
        db,
        upcoming_only,
        current_user["role"],
        barber_id=barber_id,
        start_date=start_date,
        end_date=end_date,
        admin_id=current_user["id"],
    )


@router.post(
    "/schedules/",
    response_model=AdminBarberScheduleOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_schedule(
    data: AdminBarberScheduleCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await admin_create_schedule_service(
        db,
        data,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.put("/schedules/{schedule_id}", response_model=AdminBarberScheduleOut)
async def admin_update_schedule(
    schedule_id: int,
    data: AdminBarberScheduleUpdate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await admin_update_schedule_service(
        db,
        schedule_id,
        data,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await admin_delete_schedule_service(
        db,
        schedule_id,
        current_user["role"],
        admin_id=current_user["id"],
    )
    return None

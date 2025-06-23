from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_session
from app.schemas.barber import BarberOut, BarberUpdate
from app.schemas.barber_schedule import (
    BarberScheduleCreate,
    BarberScheduleOut,
    BarberScheduleUpdate,
)
from app.services.barber_service import (
    create_schedule,
    delete_schedule,
    get_my_barber_by_id,
    get_my_schedule,
    remove_barber_photo,
    update_my_barber,
    update_schedule,
    upload_barber_photo,
)

router = APIRouter()


@router.post("/schedules/", response_model=BarberScheduleOut)
async def create_my_schedule(
    data: BarberScheduleCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await create_schedule(
        db, user_id=current_user["id"], data=data, role=current_user["role"]
    )


@router.get("/schedules/", response_model=list[BarberScheduleOut])
async def get_my_schedules(
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_my_schedule(
        db, user_id=current_user["id"], role=current_user["role"]
    )


@router.put("/schedules/{schedule_id}", response_model=BarberScheduleOut)
async def update_my_schedule(
    schedule_id: int,
    data: BarberScheduleUpdate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await update_schedule(
        db,
        schedule_id,
        user_id=current_user["id"],
        data=data,
        role=current_user["role"],
    )


@router.delete("/schedules/{schedule_id}")
async def delete_my_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await delete_schedule(
        db, schedule_id, user_id=current_user["id"], role=current_user["role"]
    )


@router.get("/me", response_model=BarberOut)
async def get_my_barber_profile(
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_my_barber_by_id(
        db, user_id=current_user["id"], role=current_user["role"]
    )


@router.put("/me", response_model=BarberOut)
async def update_my_barber_profile(
    data: BarberUpdate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await update_my_barber(
        db, data, user_id=current_user["id"], role=current_user["role"]
    )


@router.post("/avatar")
async def upload_own_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    barber = await upload_barber_photo(
        db=db, user_id=current_user["id"], file=file, user_role=current_user["role"]
    )
    return {"avatar_url": barber.avatar_url}


@router.delete("/avatar")
async def delete_own_avatar(
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await remove_barber_photo(
        db=db,
        user_id=current_user["id"],
        user_role=current_user["role"],
    )
    return {"detail": "Avatar deleted"}

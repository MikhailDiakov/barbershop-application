from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_session
from app.schemas.barber import BarberCreate, BarberOut
from app.services.admin.barbers import (
    create_barber,
    delete_barber,
    get_all_barbers,
    get_barber_by_id,
    remove_barber_photo,
    upload_barber_photo,
)

router = APIRouter()


@router.get("/", response_model=list[BarberOut])
async def list_barbers(
    db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user_info)
):
    return await get_all_barbers(db, current_user["role"])


@router.get("/{barber_id}", response_model=BarberOut)
async def get_barber(
    barber_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_barber_by_id(db, barber_id, current_user["role"])


@router.post("/create", response_model=BarberOut, status_code=status.HTTP_201_CREATED)
async def add_barber(
    barber: BarberCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await create_barber(db, barber, current_user["role"])


@router.delete("/{barber_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_barber(
    barber_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await delete_barber(db, barber_id, current_user["role"])


@router.post("/{barber_id}/avatar", response_model=BarberOut)
async def upload_barber_avatar(
    barber_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await upload_barber_photo(db, barber_id, file, current_user["role"])


@router.delete("/{barber_id}/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_barber_avatar(
    barber_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await remove_barber_photo(db, barber_id, current_user["role"])

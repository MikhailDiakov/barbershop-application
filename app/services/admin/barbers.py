import re

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hash import get_password_hash
from app.models.barber import Barber
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.barber import BarberCreate
from app.services.admin.utils import ensure_admin
from app.services.s3_service import delete_file_from_s3, upload_file_to_s3
from app.utils.selectors.selectors import (
    get_barber_by_id as get_barber_by_id_without_admin,
)
from app.utils.selectors.selectors import (
    get_user_by_id,
    get_user_by_phone,
    get_user_by_username,
)


async def create_barber(
    db: AsyncSession, barber_data: BarberCreate, user_role: RoleEnum
):
    ensure_admin(user_role)

    if await get_user_by_username(db, barber_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    if await get_user_by_phone(db, barber_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already exists",
        )

    barber_role_id = RoleEnum.BARBER.value

    user = User(
        username=barber_data.username,
        hashed_password=get_password_hash(barber_data.password),
        phone=barber_data.phone,
        role_id=barber_role_id,
    )
    db.add(user)
    await db.flush()

    barber = Barber(
        user_id=user.id,
        full_name=barber_data.full_name,
        avatar_url=None,
    )
    db.add(barber)
    await db.commit()
    await db.refresh(barber)

    return barber


async def get_all_barbers(db: AsyncSession, user_role: RoleEnum):
    ensure_admin(user_role)

    result = await db.execute(select(Barber))
    return result.scalars().all()


async def delete_barber(db: AsyncSession, barber_id: int, user_role: RoleEnum):
    ensure_admin(user_role)

    barber = await get_barber_by_id_without_admin(db, barber_id)
    if not barber:
        raise HTTPException(status_code=404, detail="Barber not found")

    user = await get_user_by_id(db, barber.user_id)
    if user:
        user.role_id = RoleEnum.CLIENT.value
        db.add(user)

    await db.delete(barber)
    await db.commit()


async def get_barber_by_id(db: AsyncSession, barber_id: int, user_role: str):
    ensure_admin(user_role)

    barber = await get_barber_by_id_without_admin(db, barber_id)
    if not barber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Barber not found"
        )

    return barber


async def upload_barber_photo(
    db: AsyncSession, barber_id: int, file: UploadFile, user_role: str
):
    ensure_admin(user_role)

    barber = await get_barber_by_id_without_admin(db, barber_id)
    if not barber:
        raise HTTPException(status_code=404, detail="Barber not found")

    content = await file.read()

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    if barber.avatar_url:
        match = re.search(r"/barbers/.*$", barber.avatar_url)
        if match:
            key = match.group(0).lstrip("/")
            await delete_file_from_s3(key)

    url = await upload_file_to_s3(content, file.filename, file.content_type)

    stmt = update(Barber).where(Barber.id == barber_id).values(avatar_url=url)
    await db.execute(stmt)
    await db.commit()

    barber.avatar_url = url
    return barber


async def remove_barber_photo(db: AsyncSession, barber_id: int, user_role: str):
    ensure_admin(user_role)

    barber = await get_barber_by_id_without_admin(db, barber_id)
    if not barber:
        raise HTTPException(status_code=404, detail="Barber not found")

    if not barber.avatar_url:
        raise HTTPException(status_code=400, detail="Barber has no avatar to delete")

    match = re.search(r"/barbers/.*$", barber.avatar_url)
    if match:
        key = match.group(0).lstrip("/")
        await delete_file_from_s3(key)

    stmt = update(Barber).where(Barber.id == barber_id).values(avatar_url=None)
    await db.execute(stmt)
    await db.commit()

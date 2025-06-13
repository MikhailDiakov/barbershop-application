import re

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.barber import Barber
from app.models.enums import RoleEnum
from app.services.s3_service import delete_file_from_s3, upload_file_to_s3
from app.utils.queries import get_barber_by_user_id


def ensure_barber(role: str):
    if int(role) != RoleEnum.BARBER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: only barbers can perform this action",
        )


async def upload_barber_photo(
    db: AsyncSession, barber_id: int, file: UploadFile, user_role: str
):
    ensure_barber(user_role)

    barber = await get_barber_by_user_id(db, barber_id)
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

    stmt = update(Barber).where(Barber.id == barber.id).values(avatar_url=url)
    await db.execute(stmt)
    await db.commit()

    barber.avatar_url = url
    return barber


async def remove_barber_photo(db: AsyncSession, barber_id: int, user_role: str):
    ensure_barber(user_role)

    barber = await get_barber_by_user_id(db, barber_id)
    if not barber:
        raise HTTPException(status_code=404, detail="Barber not found")

    if not barber.avatar_url:
        raise HTTPException(status_code=400, detail="Barber has no avatar to delete")

    match = re.search(r"/barbers/.*$", barber.avatar_url)
    if match:
        key = match.group(0).lstrip("/")
        await delete_file_from_s3(key)

    stmt = update(Barber).where(Barber.id == barber.id).values(avatar_url=None)
    await db.execute(stmt)
    await db.commit()

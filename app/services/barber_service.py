import re
from datetime import datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.barber import Barber
from app.models.barberschedule import BarberSchedule
from app.models.enums import RoleEnum
from app.services.s3_service import delete_file_from_s3, upload_file_to_s3
from app.utils.selectors.barber import get_barber_by_user_id
from app.utils.selectors.schedule import get_schedule_by_id
from app.utils.time_correction import check_time_overlap, trim_time


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


async def create_schedule(db: AsyncSession, barber_id: int, data, role: str):
    ensure_barber(role)

    start_time_trimmed = trim_time(data.start_time)
    end_time_trimmed = trim_time(data.end_time)
    now = datetime.utcnow()

    schedule_start = datetime.combine(data.date, start_time_trimmed)
    if schedule_start < now:
        raise HTTPException(
            status_code=400,
            detail="Cannot create a schedule in the past",
        )

    if await check_time_overlap(
        db, barber_id, data.date, start_time_trimmed, end_time_trimmed
    ):
        raise HTTPException(
            status_code=400,
            detail="This time slot overlaps with an existing schedule",
        )
    schedule_data = data.dict()
    schedule_data["start_time"] = start_time_trimmed
    schedule_data["end_time"] = end_time_trimmed

    schedule = BarberSchedule(barber_id=barber_id, **schedule_data)
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def get_my_schedule(db: AsyncSession, barber_id: int, role: str):
    ensure_barber(role)

    now = datetime.now()

    result = await db.execute(
        select(BarberSchedule).where(
            BarberSchedule.barber_id == barber_id,
            (BarberSchedule.date > now.date())
            | (
                (BarberSchedule.date == now.date())
                & (BarberSchedule.start_time >= now.time())
            ),
        )
    )
    return result.scalars().all()


async def update_schedule(
    db: AsyncSession, schedule_id: int, barber_id: int, data, role: str
):
    ensure_barber(role)

    schedule = await get_schedule_by_id(db, schedule_id, barber_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if not schedule.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot update schedule: this slot has already been booked by a client",
        )

    update_data = data.dict(exclude_unset=True)

    if "start_time" in update_data and update_data["start_time"] is not None:
        update_data["start_time"] = trim_time(update_data["start_time"])
    if "end_time" in update_data and update_data["end_time"] is not None:
        update_data["end_time"] = trim_time(update_data["end_time"])

    new_start = update_data.get("start_time", schedule.start_time)
    new_end = update_data.get("end_time", schedule.end_time)
    schedule_date = update_data.get("data", schedule.date)

    now = datetime.utcnow()
    schedule_start = datetime.combine(schedule_date, new_start)

    if schedule_start < now:
        raise HTTPException(
            status_code=400,
            detail="Cannot set schedule start time in the past",
        )

    if schedule_start < now:
        raise HTTPException(
            status_code=400,
            detail="Cannot set schedule start time in the past",
        )

    if await check_time_overlap(
        db,
        barber_id,
        schedule_date,
        new_start,
        new_end,
        exclude_schedule_id=schedule_id,
    ):
        raise HTTPException(
            status_code=400,
            detail="This time slot overlaps with an existing schedule",
        )

    for key, value in update_data.items():
        setattr(schedule, key, value)

    await db.commit()
    await db.refresh(schedule)
    return schedule


async def delete_schedule(
    db: AsyncSession, schedule_id: int, barber_id: int, role: str
):
    ensure_barber(role)
    schedule = await get_schedule_by_id(db, schedule_id, barber_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await db.delete(schedule)
    await db.commit()
    return {"detail": "Schedule deleted"}

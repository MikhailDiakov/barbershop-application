import re
from datetime import datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.barber import Barber
from app.models.barberschedule import BarberSchedule
from app.models.enums import RoleEnum
from app.schemas.barber import BarberUpdate
from app.services.s3_service import delete_file_from_s3, upload_file_to_s3
from app.utils.logger import logger
from app.utils.selectors.barber import get_barber_by_user_id
from app.utils.selectors.schedule import get_schedule_by_id
from app.utils.time_correction import check_time_overlap, trim_time


def ensure_barber(role: str):
    if int(role) != RoleEnum.BARBER.value:
        logger.warning("Access denied: user is not a barber", extra={"role": role})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: only barbers can perform this action",
        )


async def upload_barber_photo(
    db: AsyncSession, user_id: int, file: UploadFile, user_role: str
):
    ensure_barber(user_role)
    logger.info("Attempting to upload barber photo", extra={"user_id": user_id})

    barber = await get_barber_by_user_id(db, user_id)
    if not barber:
        logger.warning("Barber not found for photo upload", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="Barber not found")

    barber_id = barber.id
    content = await file.read()

    if not file.content_type.startswith("image/"):
        logger.warning(
            "Upload failed: non-image file",
            extra={
                "filename": file.filename,
                "content_type": file.content_type,
                "user_id": user_id,
            },
        )
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    if barber.avatar_url:
        match = re.search(r"/barbers/.*$", barber.avatar_url)
        if match:
            key = match.group(0).lstrip("/")
            await delete_file_from_s3(key)
            logger.info(
                "Deleted old barber avatar from S3",
                extra={"barber_id": barber_id, "s3_key": key},
            )

    url = await upload_file_to_s3(content, file.filename, file.content_type)

    stmt = update(Barber).where(Barber.id == barber_id).values(avatar_url=url)
    await db.execute(stmt)
    await db.commit()

    logger.info(
        "Uploaded new barber photo", extra={"barber_id": barber_id, "avatar_url": url}
    )
    barber.avatar_url = url
    return barber


async def remove_barber_photo(db: AsyncSession, user_id: int, user_role: str):
    ensure_barber(user_role)
    logger.info("Attempting to remove barber photo", extra={"user_id": user_id})

    barber = await get_barber_by_user_id(db, user_id)
    if not barber:
        logger.warning("Barber not found for photo removal", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="Barber not found")

    barber_id = barber.id
    if not barber.avatar_url:
        logger.warning(
            "Attempted to delete avatar, but barber has no avatar",
            extra={"barber_id": barber_id},
        )
        raise HTTPException(status_code=400, detail="Barber has no avatar to delete")

    match = re.search(r"/barbers/.*$", barber.avatar_url)
    if match:
        key = match.group(0).lstrip("/")
        await delete_file_from_s3(key)
        logger.info(
            "Deleted barber avatar from S3",
            extra={"barber_id": barber_id, "s3_key": key},
        )

    stmt = update(Barber).where(Barber.id == barber_id).values(avatar_url=None)
    await db.execute(stmt)
    await db.commit()

    logger.info("Removed barber avatar from DB", extra={"barber_id": barber_id})


async def create_schedule(db: AsyncSession, user_id: int, data, role: str):
    ensure_barber(role)
    logger.info("Attempting to create schedule", extra={"user_id": user_id})

    barber = await get_barber_by_user_id(db, user_id)
    if not barber:
        logger.warning(
            "Barber not found when creating schedule", extra={"user_id": user_id}
        )
        raise HTTPException(status_code=404, detail="Barber not found")
    barber_id = barber.id
    start_time_trimmed = trim_time(data.start_time)
    end_time_trimmed = trim_time(data.end_time)
    now = datetime.utcnow()

    schedule_start = datetime.combine(data.date, start_time_trimmed)
    if schedule_start < now:
        logger.warning(
            "Attempted to create schedule in the past",
            extra={
                "barber_id": barber_id,
                "schedule_start": schedule_start.isoformat(),
            },
        )
        raise HTTPException(
            status_code=400,
            detail="Cannot create a schedule in the past",
        )

    if await check_time_overlap(
        db, barber_id, data.date, start_time_trimmed, end_time_trimmed
    ):
        logger.warning(
            "Schedule overlaps with existing slot",
            extra={
                "barber_id": barber_id,
                "date": str(data.date),
                "start_time": str(start_time_trimmed),
                "end_time": str(end_time_trimmed),
            },
        )
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

    logger.info(
        "Barber schedule created",
        extra={
            "barber_id": barber_id,
            "date": str(schedule.date),
            "start_time": str(schedule.start_time),
            "end_time": str(schedule.end_time),
        },
    )

    return schedule


async def get_my_schedule(db: AsyncSession, user_id: int, role: str):
    ensure_barber(role)
    logger.info("Attempting to retrieve barber schedule", extra={"user_id": user_id})

    barber = await get_barber_by_user_id(db, user_id)
    if not barber:
        logger.warning(
            "Barber not found when retrieving schedule", extra={"user_id": user_id}
        )
        raise HTTPException(status_code=404, detail="Barber not found")

    now = datetime.now()

    result = await db.execute(
        select(BarberSchedule).where(
            BarberSchedule.barber_id == barber.id,
            (BarberSchedule.date > now.date())
            | (
                (BarberSchedule.date == now.date())
                & (BarberSchedule.start_time >= now.time())
            ),
        )
    )
    logger.info(
        "Barber schedule retrieved",
        extra={"barber_id": barber.id, "retrieved_at": now.isoformat()},
    )
    return result.scalars().all()


async def update_schedule(
    db: AsyncSession, schedule_id: int, user_id: int, data, role: str
):
    ensure_barber(role)
    logger.info(
        "Attempting to update schedule",
        extra={"schedule_id": schedule_id, "user_id": user_id},
    )

    barber = await get_barber_by_user_id(db, user_id)
    if not barber:
        logger.warning(
            "Barber not found when retrieving schedule", extra={"user_id": user_id}
        )
        raise HTTPException(status_code=404, detail="Barber not found")

    schedule = await get_schedule_by_id(db, schedule_id, barber.id)
    if not schedule:
        logger.warning(
            "Schedule not found for update",
            extra={"schedule_id": schedule_id, "barber_id": barber.id},
        )
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_data = data.dict(exclude_unset=True)

    if "start_time" in update_data and update_data["start_time"] is not None:
        update_data["start_time"] = trim_time(update_data["start_time"])
    if "end_time" in update_data and update_data["end_time"] is not None:
        update_data["end_time"] = trim_time(update_data["end_time"])

    new_start = update_data.get("start_time", schedule.start_time)
    new_end = update_data.get("end_time", schedule.end_time)
    schedule_date = update_data.get("date", schedule.date)

    if new_start >= new_end:
        logger.warning(
            "Start time is not earlier than end time",
            extra={
                "schedule_id": schedule_id,
                "start": str(new_start),
                "end": str(new_end),
            },
        )
        raise HTTPException(
            status_code=400,
            detail="Start time must be earlier than end time",
        )

    now = datetime.utcnow()
    schedule_start = datetime.combine(schedule_date, new_start)

    if schedule_start < now:
        logger.warning(
            "Attempted to update schedule with past time",
            extra={
                "schedule_id": schedule_id,
                "user_id": user_id,
                "new_start": str(new_start),
                "new_end": str(new_end),
            },
        )
        raise HTTPException(
            status_code=400,
            detail="Cannot set schedule start time in the past",
        )

    if await check_time_overlap(
        db,
        barber.id,
        schedule_date,
        new_start,
        new_end,
        exclude_schedule_id=schedule_id,
    ):
        logger.warning(
            "Schedule update failed due to overlap",
            extra={
                "schedule_id": schedule_id,
                "barber_id": barber.id,
                "start": str(new_start),
                "end": str(new_end),
            },
        )
        raise HTTPException(
            status_code=400,
            detail="This time slot overlaps with an existing schedule",
        )

    for key, value in update_data.items():
        setattr(schedule, key, value)

    await db.commit()
    await db.refresh(schedule)

    logger.info(
        "Schedule updated successfully",
        extra={"schedule_id": schedule.id, "barber_id": barber.id},
    )
    return schedule


async def delete_schedule(db: AsyncSession, schedule_id: int, user_id: int, role: str):
    ensure_barber(role)
    logger.info(
        "Attempting to delete schedule",
        extra={"schedule_id": schedule_id, "user_id": user_id},
    )

    barber = await get_barber_by_user_id(db, user_id)

    if not barber:
        logger.warning(
            "Barber not found when deleting schedule",
            extra={"user_id": user_id},
        )
        raise HTTPException(status_code=404, detail="Barber not found")

    schedule = await get_schedule_by_id(db, schedule_id, barber.id)
    if not schedule:
        logger.warning(
            "Schedule not found for deletion",
            extra={"schedule_id": schedule_id, "barber_id": barber.id},
        )
        raise HTTPException(status_code=404, detail="Schedule not found")

    if not schedule.is_active:
        logger.warning(
            "Attempted to delete booked schedule",
            extra={"schedule_id": schedule.id, "barber_id": barber.id},
        )
        raise HTTPException(
            status_code=400,
            detail="Cannot delete schedule: this slot has already been booked by a client. Please cancel the appointment first.",
        )

    await db.delete(schedule)
    await db.commit()

    logger.info(
        "Schedule deleted successfully",
        extra={"schedule_id": schedule.id, "barber_id": barber.id},
    )
    return {"detail": "Schedule deleted"}


async def get_my_barber_by_id(db: AsyncSession, user_id: int, role: str) -> Barber:
    ensure_barber(role)
    logger.info("Attempting to retrieve barber", extra={"user_id": user_id})

    barber = await get_barber_by_user_id(db, user_id)
    if not barber:
        logger.warning("Barber not found when retrieving", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="Barber not found")

    logger.info("Barber retrieved successfully", extra={"barber_id": barber.id})
    return barber


async def update_my_barber(
    db: AsyncSession, user_id: int, data: BarberUpdate, role: str
) -> Barber:
    ensure_barber(role)
    logger.info("Attempting to update barber info", extra={"user_id": user_id})

    barber = await get_barber_by_user_id(db, user_id)
    if not barber:
        logger.warning("Barber not found for update", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="Barber not found")

    barber.full_name = data.full_name
    await db.commit()
    await db.refresh(barber)

    logger.info("Barber info updated", extra={"barber_id": barber.id})
    return barber

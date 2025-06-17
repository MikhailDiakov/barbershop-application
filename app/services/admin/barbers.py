import re
from datetime import date, datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hash import get_password_hash
from app.models.appointment import Appointment
from app.models.barber import Barber
from app.models.barberschedule import BarberSchedule
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.barber import BarberCreate
from app.schemas.barber_schedule import (
    AdminBarberScheduleCreate,
    AdminBarberScheduleUpdate,
)
from app.services.admin.utils import ensure_admin
from app.services.s3_service import delete_file_from_s3, upload_file_to_s3
from app.utils.selectors.barber import (
    get_barber_by_id as get_barber_by_id_without_admin,
)
from app.utils.selectors.schedule import (
    get_schedule_by_id_simple,
    select_all_schedules_flat,
)
from app.utils.selectors.user import (
    get_user_by_id,
    get_user_by_phone,
    get_user_by_username,
)
from app.utils.time_correction import check_time_overlap, trim_time


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


async def admin_get_all_schedules(
    db: AsyncSession,
    upcoming_only: bool,
    role: RoleEnum,
    barber_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
):
    ensure_admin(role)
    return await select_all_schedules_flat(
        db, upcoming_only, barber_id, start_date, end_date
    )


async def admin_create_schedule_service(
    db: AsyncSession, data: AdminBarberScheduleCreate, role: RoleEnum
):
    ensure_admin(role)

    barber = await get_barber_by_id_without_admin(db, data.barber_id)
    if not barber:
        raise HTTPException(status_code=404, detail="Barber not found")

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
        db, data.barber_id, data.date, start_time_trimmed, end_time_trimmed
    ):
        raise HTTPException(
            status_code=400,
            detail="This time slot overlaps with an existing schedule",
        )

    schedule = BarberSchedule(
        barber_id=data.barber_id,
        date=data.date,
        start_time=start_time_trimmed,
        end_time=end_time_trimmed,
        is_active=data.is_active,
    )

    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def admin_update_schedule_service(
    db: AsyncSession,
    schedule_id: int,
    data: AdminBarberScheduleUpdate,
    role: RoleEnum,
):
    ensure_admin(role)

    schedule = await get_schedule_by_id_simple(db, schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if not schedule.is_active:
        raise HTTPException(
            status_code=400,
            detail="This slot is already booked by a client. Please delete the client's appointment first to update the schedule.",
        )

    update_data = data.dict(exclude_unset=True)

    if "barber_id" in update_data:
        barber = await get_barber_by_id_without_admin(db, update_data["barber_id"])
        if not barber:
            raise HTTPException(status_code=404, detail="Barber not found")

    date = update_data.get("date", schedule.date)
    start_time = trim_time(update_data.get("start_time", schedule.start_time))
    end_time = trim_time(update_data.get("end_time", schedule.end_time))
    barber_id = update_data.get("barber_id", schedule.barber_id)

    schedule_start = datetime.combine(date, start_time)
    if schedule_start < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Cannot update to a schedule in the past",
        )

    if await check_time_overlap(
        db, barber_id, date, start_time, end_time, exclude_schedule_id=schedule_id
    ):
        raise HTTPException(
            status_code=400,
            detail="This time slot overlaps with an existing schedule",
        )
    old_barber_id = schedule.barber_id

    schedule.barber_id = barber_id
    schedule.date = date
    schedule.start_time = start_time
    schedule.end_time = end_time

    if "is_active" in update_data:
        schedule.is_active = update_data["is_active"]

    result = await db.execute(
        select(Appointment).where(Appointment.schedule_id == schedule_id)
    )
    appointment = result.scalar_one_or_none()

    if appointment:
        appointment.appointment_time = schedule_start
        if old_barber_id != barber_id:
            appointment.barber_id = barber_id
        db.add(appointment)

    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def admin_delete_schedule_service(
    db: AsyncSession, schedule_id: int, role: RoleEnum
):
    ensure_admin(role)

    schedule = await get_schedule_by_id_simple(db, schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await db.delete(schedule)
    await db.commit()

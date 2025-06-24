from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.barberschedule import BarberSchedule
from app.schemas.appointment import AppointmentCreate
from app.services.admin.utils import ensure_admin
from app.utils.celery_tasks.sms import send_sms_task
from app.utils.logger import logger
from app.utils.selectors.schedule import get_schedule_by_id_simple


async def admin_get_appointments_service(
    db: AsyncSession,
    upcoming_only: bool,
    skip: int,
    limit: int,
    role: str,
    admin_id: int,
):
    ensure_admin(role)

    logger.info(
        "Admin fetching appointments",
        extra={
            "admin_id": admin_id,
            "upcoming_only": upcoming_only,
            "skip": skip,
            "limit": limit,
            "role": role,
        },
    )

    query = select(Appointment)
    if upcoming_only:
        now = datetime.utcnow()
        query = query.where(Appointment.appointment_time >= now)
    query = query.offset(skip).limit(limit).order_by(Appointment.appointment_time.asc())

    result = await db.execute(query)
    appointments = result.scalars().all()

    logger.info(
        "Admin fetched appointments",
        extra={
            "admin_id": admin_id,
            "count": len(appointments),
            "upcoming_only": upcoming_only,
        },
    )
    return appointments


async def admin_create_appointment_service(
    db: AsyncSession, data: AppointmentCreate, role: str, admin_id: int
):
    ensure_admin(role)

    logger.info(
        "Admin attempt to create appointment",
        extra={
            "admin_id": admin_id,
            "barber_id": data.barber_id,
            "schedule_id": data.schedule_id,
        },
    )

    schedule = await get_schedule_by_id_simple(db, data.schedule_id)
    if not schedule or not schedule.is_active:
        logger.warning(
            "Schedule not available for admin appointment",
            extra={"schedule_id": data.schedule_id, "admin_id": admin_id},
        )
        raise HTTPException(400, "Selected time slot is not available")

    if not data.client_name or not data.client_phone:
        logger.warning(
            "Missing name or phone for admin appointment",
            extra={"schedule_id": data.schedule_id, "admin_id": admin_id},
        )
        raise HTTPException(400, "Name and phone required for admin booking")

    appointment_dt = datetime.combine(schedule.date, schedule.start_time)

    appointment = Appointment(
        barber_id=data.barber_id,
        client_name=data.client_name,
        client_phone=data.client_phone,
        appointment_time=appointment_dt,
        status="scheduled",
        client_id=None,
        schedule_id=data.schedule_id,
    )

    db.add(appointment)
    schedule.is_active = False
    await db.commit()
    await db.refresh(appointment)

    logger.info(
        "Admin created appointment",
        extra={
            "admin_id": admin_id,
            "appointment_id": appointment.id,
            "barber_id": data.barber_id,
            "client_name": data.client_name,
            "appointment_time": appointment_dt.isoformat(),
        },
    )

    send_sms_task.delay(
        to_phone=data.client_phone,
        message=(
            f"Dear {data.client_name}, your appointment is confirmed for "
            f"{appointment_dt.strftime('%A, %B %d, %Y at %I:%M %p')}. "
            "We look forward to seeing you!"
        ),
    )

    logger.info(
        "Confirmation SMS sent",
        extra={"appointment_id": appointment.id, "admin_id": admin_id},
    )

    now = datetime.utcnow()
    remind_time = appointment_dt - timedelta(hours=2)
    seconds_until_reminder = (remind_time - now).total_seconds()

    if seconds_until_reminder > 0:
        send_sms_task.apply_async(
            args=(
                data.client_phone,
                f"Dear {data.client_name}, this is a reminder of your appointment scheduled for "
                f"{appointment_dt.strftime('%A, %B %d, %Y at %I:%M %p')}. See you soon!",
            ),
            countdown=seconds_until_reminder,
        )
        logger.info(
            "Reminder SMS scheduled",
            extra={
                "admin_id": admin_id,
                "client_phone": data.client_phone,
                "reminder_in_seconds": round(seconds_until_reminder),
            },
        )

    return appointment


async def admin_delete_appointment_service(
    db: AsyncSession,
    appointment_id: int,
    role: str,
    admin_id: int,
):
    ensure_admin(role)
    logger.info(
        "Admin attempt to delete appointment",
        extra={"appointment_id": appointment_id, "role": role, "admin_id": admin_id},
    )

    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        logger.warning(
            "Appointment not found for deletion",
            extra={"appointment_id": appointment_id, "admin_id": admin_id},
        )
        raise HTTPException(status_code=404, detail="Appointment not found")

    result = await db.execute(
        select(BarberSchedule).where(BarberSchedule.id == appointment.schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        logger.warning(
            "Related schedule not found for appointment deletion",
            extra={
                "appointment_id": appointment_id,
                "schedule_id": appointment.schedule_id,
                "admin_id": admin_id,
            },
        )
        raise HTTPException(status_code=404, detail="Related schedule not found")

    await db.delete(appointment)

    schedule.is_active = True
    db.add(schedule)

    await db.commit()
    logger.info(
        "Admin deleted appointment and reactivated schedule",
        extra={
            "appointment_id": appointment.id,
            "schedule_id": schedule.id,
            "barber_id": appointment.barber_id,
            "admin_id": admin_id,
        },
    )

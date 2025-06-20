from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.barberschedule import BarberSchedule
from app.schemas.appointment import AppointmentCreate
from app.services.admin.utils import ensure_admin
from app.utils.celery_tasks.sms import send_sms_task
from app.utils.selectors.schedule import get_schedule_by_id_simple


async def admin_get_appointments_service(
    db: AsyncSession,
    upcoming_only: bool,
    skip: int,
    limit: int,
    role: str,
):
    ensure_admin(role)
    query = select(Appointment)
    if upcoming_only:
        now = datetime.utcnow()
        query = query.where(Appointment.appointment_time >= now)
    query = query.offset(skip).limit(limit).order_by(Appointment.appointment_time.asc())
    result = await db.execute(query)
    return result.scalars().all()


async def admin_create_appointment_service(
    db: AsyncSession, data: AppointmentCreate, role: str
):
    ensure_admin(role)

    schedule = await get_schedule_by_id_simple(db, data.schedule_id)
    if not schedule or not schedule.is_active:
        raise HTTPException(400, "Selected time slot is not available")

    if not data.client_name or not data.client_phone:
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

    send_sms_task.delay(
        to_phone=data.client_phone,
        message=(
            f"Dear {data.client_name}, your appointment is confirmed for "
            f"{appointment_dt.strftime('%A, %B %d, %Y at %I:%M %p')}. "
            "We look forward to seeing you!"
        ),
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

    return appointment


async def admin_delete_appointment_service(
    db: AsyncSession,
    appointment_id: int,
    role: str,
):
    ensure_admin(role)

    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    result = await db.execute(
        select(BarberSchedule).where(BarberSchedule.id == appointment.schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Related schedule not found")

    await db.delete(appointment)

    schedule.is_active = True
    db.add(schedule)

    await db.commit()

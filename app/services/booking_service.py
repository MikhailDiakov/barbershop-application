from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.appointment import Appointment
from app.models.barber import Barber
from app.models.review import Review
from app.schemas.appointment import AppointmentCreate
from app.schemas.barber import (
    BarberOutwithReviews,
    BarberOutwithReviewsDetailed,
    ReviewReadForBarber,
)
from app.schemas.barber_schedule import BarberWithScheduleAndReviewsOut
from app.utils.celery_tasks.sms import send_sms_task
from app.utils.redis_client import get_barber_rating, save_barber_rating
from app.utils.selectors.barber import get_all_barbers
from app.utils.selectors.reviews import get_barber_rating_from_db
from app.utils.selectors.schedule import (
    get_barbers_with_schedules,
    get_schedule_by_id_simple,
)
from app.utils.selectors.user import get_user_by_id


async def create_appointment_service(
    db: AsyncSession, data: AppointmentCreate, current_user: dict | None
):
    schedule = await get_schedule_by_id_simple(db, data.schedule_id)
    if not schedule or not schedule.is_active:
        raise HTTPException(400, "Selected time slot is not available")

    appointment_dt = datetime.combine(schedule.date, schedule.start_time)

    if current_user:
        user = await get_user_by_id(db, current_user["id"])
        if not user:
            raise HTTPException(400, "User not found")

        client_name = user.username
        client_phone = user.phone
    else:
        if not data.client_name or not data.client_phone:
            raise HTTPException(400, "Name and phone required for anonymous booking")
        client_name = data.client_name
        client_phone = data.client_phone

    appointment = Appointment(
        barber_id=data.barber_id,
        client_name=client_name,
        client_phone=client_phone,
        appointment_time=appointment_dt,
        status="scheduled",
        client_id=current_user["id"] if current_user else None,
        schedule_id=data.schedule_id,
    )

    db.add(appointment)
    schedule.is_active = False

    await db.commit()
    await db.refresh(appointment)

    send_sms_task.delay(
        to_phone=client_phone,
        message=(
            f"Dear {client_name}, your appointment is confirmed for "
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
                client_phone,
                f"Dear {client_name}, this is a reminder of your appointment scheduled for "
                f"{appointment_dt.strftime('%A, %B %d, %Y at %I:%M %p')}. See you soon!",
            ),
            countdown=seconds_until_reminder,
        )
    return appointment


async def get_appointments_by_user(db: AsyncSession, user_id: int, upcoming_only: bool):
    query = select(Appointment).where(Appointment.client_id == user_id)
    if upcoming_only:
        now = datetime.utcnow()
        query = query.where(Appointment.appointment_time >= now)
    result = await db.execute(query)
    return result.scalars().all()


async def get_barbers_with_ratings(db: AsyncSession) -> List[BarberOutwithReviews]:
    barbers = await get_all_barbers(db)
    result = []

    for barber in barbers:
        cached_rating = await get_barber_rating(barber.id)

        if cached_rating:
            avg_rating, reviews_count = cached_rating
        else:
            avg_rating, reviews_count = await get_barber_rating_from_db(db, barber.id)
            await save_barber_rating(barber.id, avg_rating, reviews_count)

        barber_out = BarberOutwithReviews.from_orm(barber).copy(
            update={
                "avg_rating": avg_rating,
                "reviews_count": reviews_count,
            }
        )
        result.append(barber_out)

    return result


async def get_barber_detailed_info(
    db: AsyncSession, barber_id: int
) -> BarberOutwithReviewsDetailed | None:
    barber = await db.get(
        Barber,
        barber_id,
        options=[joinedload(Barber.reviews).joinedload(Review.client)],
    )

    if not barber:
        raise HTTPException(status_code=404, detail="Barber not found")

    cached_rating = await get_barber_rating(barber.id)
    if cached_rating:
        avg_rating, reviews_count = cached_rating
    else:
        avg_rating, reviews_count = await get_barber_rating_from_db(db, barber.id)
        await save_barber_rating(barber.id, avg_rating, reviews_count)

    reviews = [
        ReviewReadForBarber(
            id=r.id,
            client_name=r.client.username,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in barber.reviews
        if r.is_approved
    ]

    return BarberOutwithReviewsDetailed(
        id=barber.id,
        full_name=barber.full_name,
        avatar_url=barber.avatar_url,
        avg_rating=avg_rating,
        reviews_count=reviews_count,
        reviews=reviews,
    )


async def get_barbers_with_schedules_and_ratings(
    db: AsyncSession,
) -> list[BarberWithScheduleAndReviewsOut]:
    barbers = await get_barbers_with_schedules(db)
    result = []

    for barber in barbers:
        cached_rating = await get_barber_rating(barber.id)

        if cached_rating:
            avg_rating, reviews_count = cached_rating
        else:
            avg_rating, reviews_count = await get_barber_rating_from_db(db, barber.id)
            await save_barber_rating(barber.id, avg_rating, reviews_count)

        barber_out = BarberWithScheduleAndReviewsOut.from_orm(barber).copy(
            update={
                "avg_rating": avg_rating,
                "reviews_count": reviews_count,
            }
        )
        result.append(barber_out)

    return result

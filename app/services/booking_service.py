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
from app.services.barber_rating import get_rating_for_barber
from app.utils.celery_tasks.sms import send_sms_task
from app.utils.logger import logger
from app.utils.selectors.barber import get_all_barbers
from app.utils.selectors.schedule import (
    get_barbers_with_schedules,
    get_schedule_by_id_simple,
)
from app.utils.selectors.user import get_user_by_id


async def create_appointment_service(
    db: AsyncSession, data: AppointmentCreate, current_user: dict | None
):
    logger.info(
        "Attempting to create appointment", extra={"schedule_id": data.schedule_id}
    )

    schedule = await get_schedule_by_id_simple(db, data.schedule_id)
    if not schedule or not schedule.is_active:
        logger.warning(
            "Schedule not found or not active during appointment creation",
            extra={"schedule_id": data.schedule_id},
        )
        raise HTTPException(400, "Selected time slot is not available")

    appointment_dt = datetime.combine(schedule.date, schedule.start_time)

    if current_user:
        user = await get_user_by_id(db, current_user["id"])
        if not user:
            logger.warning(
                "User not found for appointment", extra={"user_id": current_user["id"]}
            )
            raise HTTPException(400, "User not found")

        client_name = user.username
        client_phone = user.phone
        logger.info(
            "Appointment being created for authenticated user",
            extra={"user_id": user.id},
        )
    else:
        if not data.client_name or not data.client_phone:
            logger.warning("Anonymous booking missing name/phone", extra={})
            raise HTTPException(400, "Name and phone required for anonymous booking")
        client_name = data.client_name
        client_phone = data.client_phone
        logger.info(
            "Appointment being created for anonymous client",
            extra={"client_phone": client_phone},
        )

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

    logger.info(
        "Appointment created successfully",
        extra={
            "appointment_id": appointment.id,
            "barber_id": data.barber_id,
            "schedule_id": data.schedule_id,
            "client_phone": client_phone,
        },
    )

    send_sms_task.delay(
        to_phone=client_phone,
        message=(
            f"Dear {client_name}, your appointment is confirmed for "
            f"{appointment_dt.strftime('%A, %B %d, %Y at %I:%M %p')}. "
            "We look forward to seeing you!"
        ),
    )
    logger.info("Confirmation SMS sent", extra={"appointment_id": appointment.id})

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
        logger.info("Reminder SMS scheduled", extra={"appointment_id": appointment.id})

    return appointment


async def get_appointments_by_user(db: AsyncSession, user_id: int, upcoming_only: bool):
    logger.info(
        "Fetching appointments for user",
        extra={"user_id": user_id, "upcoming_only": upcoming_only},
    )

    query = select(Appointment).where(Appointment.client_id == user_id)
    if upcoming_only:
        now = datetime.utcnow()
        query = query.where(Appointment.appointment_time >= now)

    result = await db.execute(query)
    appointments = result.scalars().all()

    logger.info(
        "Appointments fetched",
        extra={"user_id": user_id, "appointment_count": len(appointments)},
    )

    return appointments


async def get_barbers_with_ratings(db: AsyncSession) -> List[BarberOutwithReviews]:
    logger.info("Fetching barbers with ratings")

    barbers = await get_all_barbers(db)
    result = []

    for barber in barbers:
        avg_rating, reviews_count = await get_rating_for_barber(db, barber.id)

        barber_out = BarberOutwithReviews.from_orm(barber).copy(
            update={
                "avg_rating": avg_rating,
                "reviews_count": reviews_count,
            }
        )
        result.append(barber_out)

    logger.info("Barbers with ratings fetched", extra={"barber_count": len(result)})
    return result


async def get_barber_detailed_info(
    db: AsyncSession, barber_id: int
) -> BarberOutwithReviewsDetailed | None:
    logger.info("Fetching detailed barber info", extra={"barber_id": barber_id})

    barber = await db.get(
        Barber,
        barber_id,
        options=[joinedload(Barber.reviews).joinedload(Review.client)],
    )

    if not barber:
        logger.warning(
            "Barber not found in detailed info", extra={"barber_id": barber_id}
        )
        raise HTTPException(status_code=404, detail="Barber not found")

    avg_rating, reviews_count = await get_rating_for_barber(db, barber.id)

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
    logger.info(
        "Detailed barber info fetched",
        extra={
            "barber_id": barber.id,
            "reviews_count": len(reviews),
        },
    )

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
    logger.info("Fetching barbers with schedules and ratings")

    barbers = await get_barbers_with_schedules(db)
    result = []

    for barber in barbers:
        avg_rating, reviews_count = await get_rating_for_barber(db, barber.id)

        barber_out = BarberWithScheduleAndReviewsOut.from_orm(barber).copy(
            update={
                "avg_rating": avg_rating,
                "reviews_count": reviews_count,
            }
        )
        result.append(barber_out)

    logger.info(
        "Barbers with schedules and ratings fetched",
        extra={"barber_count": len(result)},
    )

    return result

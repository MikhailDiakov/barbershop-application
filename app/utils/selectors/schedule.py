from datetime import date, datetime

from sqlalchemy import and_, asc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_loader_criteria

from app.models import Barber, BarberSchedule


async def get_schedule_by_id(
    db: AsyncSession, schedule_id: int, barber_id: int
) -> BarberSchedule | None:
    result = await db.execute(
        select(BarberSchedule).where(
            BarberSchedule.id == schedule_id,
            BarberSchedule.barber_id == barber_id,
        )
    )
    return result.scalar_one_or_none()


async def get_schedule_by_id_simple(
    db: AsyncSession, schedule_id: int
) -> BarberSchedule | None:
    result = await db.execute(
        select(BarberSchedule).where(BarberSchedule.id == schedule_id)
    )
    return result.scalar_one_or_none()


async def get_barbers_with_schedules(db: AsyncSession) -> list[Barber]:
    now = datetime.utcnow()
    today = now.date()
    current_time = now.time()

    result = await db.execute(
        select(Barber)
        .options(
            selectinload(Barber.schedules),
            with_loader_criteria(
                BarberSchedule,
                lambda s: and_(
                    s.is_active,
                    or_(
                        s.date > today,
                        and_(s.date == today, s.start_time >= current_time),
                    ),
                ),
                include_aliases=True,
            ),
        )
        .order_by(asc(Barber.id))
    )
    return result.scalars().unique().all()


async def select_all_schedules_flat(
    db: AsyncSession,
    upcoming_only: bool,
    barber_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[BarberSchedule]:
    now = datetime.utcnow()
    today = now.date()
    current_time = now.time()

    filters = []

    if upcoming_only:
        filters.append(
            and_(
                BarberSchedule.is_active,
                or_(
                    BarberSchedule.date > today,
                    and_(
                        BarberSchedule.date == today,
                        BarberSchedule.start_time >= current_time,
                    ),
                ),
            )
        )

    if barber_id:
        filters.append(BarberSchedule.barber_id == barber_id)

    if start_date:
        filters.append(BarberSchedule.date >= start_date)

    if end_date:
        filters.append(BarberSchedule.date <= end_date)

    query = select(BarberSchedule)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    return result.scalars().all()

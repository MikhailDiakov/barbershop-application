from datetime import datetime

from sqlalchemy import and_, or_, select
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
        select(Barber).options(
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
    )
    return result.scalars().unique().all()

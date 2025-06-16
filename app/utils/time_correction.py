from datetime import time

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.barberschedule import BarberSchedule


def trim_time(t: time) -> time:
    return time(t.hour, t.minute)


async def check_time_overlap(
    db: AsyncSession,
    barber_id: int,
    date_,
    start_time: time,
    end_time: time,
    exclude_schedule_id: int | None = None,
):
    query = select(BarberSchedule).where(
        BarberSchedule.barber_id == barber_id,
        BarberSchedule.date == date_,
        or_(
            and_(
                BarberSchedule.start_time <= start_time,
                BarberSchedule.end_time > start_time,
            ),
            and_(
                BarberSchedule.start_time < end_time,
                BarberSchedule.end_time >= end_time,
            ),
            and_(
                BarberSchedule.start_time >= start_time,
                BarberSchedule.end_time <= end_time,
            ),
        ),
    )
    if exclude_schedule_id:
        query = query.where(BarberSchedule.id != exclude_schedule_id)

    result = await db.execute(query)
    overlap = result.scalar_one_or_none()
    return overlap is not None

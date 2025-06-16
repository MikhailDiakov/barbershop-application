from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarberSchedule


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

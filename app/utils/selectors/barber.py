from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Barber


async def get_barber_by_username(db: AsyncSession, username: str) -> Barber | None:
    result = await db.execute(select(Barber).filter(Barber.username == username))
    return result.scalars().first()


async def get_barber_by_phone(db: AsyncSession, phone: str) -> Barber | None:
    result = await db.execute(select(Barber).filter(Barber.phone == phone))
    return result.scalars().first()


async def get_barber_by_id(db: AsyncSession, barber_id: int) -> Barber | None:
    result = await db.execute(select(Barber).filter(Barber.id == barber_id))
    return result.scalars().first()


async def get_barber_by_user_id(db: AsyncSession, user_id: int) -> Barber | None:
    stmt = select(Barber).where(Barber.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()

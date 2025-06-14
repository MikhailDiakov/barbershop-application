from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Barber, User


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def get_user_by_phone(db: AsyncSession, phone: str) -> User | None:
    result = await db.execute(select(User).filter(User.phone == phone))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


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


async def get_user_with_barber_profile_by_id(
    db: AsyncSession, user_id: int
) -> User | None:
    result = await db.execute(
        select(User).options(joinedload(User.barber_profile)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_with_barber_profile_selectin(
    db: AsyncSession, user_id: int
) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.barber_profile))
        .where(User.id == user_id)
    )
    return result.scalars().first()

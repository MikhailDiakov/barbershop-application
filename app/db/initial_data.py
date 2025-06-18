import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.hash import get_password_hash
from app.db.session import async_session
from app.models import Role, User
from app.models.enums import RoleEnum


async def create_roles(session: AsyncSession):
    roles = {
        RoleEnum.SUPERADMIN.value: "SuperAdmin",
        RoleEnum.ADMIN.value: "Admin",
        RoleEnum.BARBER.value: "Barber",
        RoleEnum.CLIENT.value: "Client",
    }
    for role_id, role_name in roles.items():
        result = await session.execute(select(Role).where(Role.id == role_id))
        if not result.scalars().first():
            session.add(Role(id=role_id, name=role_name))
    await session.commit()


async def create_superadmin(session: AsyncSession):
    result = await session.execute(
        select(User).where(User.role_id == RoleEnum.SUPERADMIN.value)
    )
    if not result.scalars().first():
        superadmin = User(
            username=settings.SUPERADMIN_LOGIN,
            hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
            phone="",
            role_id=RoleEnum.SUPERADMIN.value,
        )
        session.add(superadmin)
        await session.commit()


async def main():
    async with async_session() as session:
        await create_roles(session)
        await create_superadmin(session)


if __name__ == "__main__":
    asyncio.run(main())

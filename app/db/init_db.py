import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.hash import get_password_hash
from app.db.base import Base
from app.db.session import async_session, engine
from app.models import Role, User, appointment, barberschedule, role, user  # noqa: F401
from app.models.enums import RoleEnum


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_first_admin(db: AsyncSession):
    result = await db.execute(select(User).where(User.role_id == RoleEnum.ADMIN.value))
    admin = result.scalars().first()
    if not admin:
        admin = User(
            username=settings.ADMIN_LOGIN,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            phone="",
            role_id=RoleEnum.ADMIN.value,
        )
        db.add(admin)
        await db.commit()


async def create_roles(db: AsyncSession):
    for role_id, role_name in {
        RoleEnum.ADMIN.value: "Admin",
        RoleEnum.BARBER.value: "Barber",
        RoleEnum.CLIENT.value: "Client",
    }.items():
        result = await db.execute(select(Role).where(Role.id == role_id))
        existing = result.scalars().first()
        if not existing:
            db.add(Role(id=role_id, name=role_name))
    await db.commit()


if __name__ == "__main__":

    async def run():
        await init_db()
        async with async_session() as session:
            await create_roles(session)
            await create_first_admin(session)

    asyncio.run(run())

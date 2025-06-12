import asyncio

from app.api.deps import engine
from app.db.base import Base
from app.models import appointment, barberschedule, role, user  # noqa: F401


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
z

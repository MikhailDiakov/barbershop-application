import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_session
from app.api.routes.users import get_login_rate_limiter
from app.core.config import settings
from app.core.hash import get_password_hash
from app.db.base import Base
from app.main import app
from app.models.barber import Barber
from app.models.role import Role
from app.models.user import User

TEST_DATABASE_URL = settings.TEST_DATABASE_URL
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        session.add_all(
            [
                Role(id=0, name="superuser"),
                Role(id=1, name="admin"),
                Role(id=2, name="barber"),
                Role(id=3, name="user"),
            ]
        )
        await session.commit()

        users = [
            User(
                username=settings.SUPERADMIN_LOGIN,
                phone="+10000000000",
                hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
                role_id=0,
            ),
            User(
                username="admin",
                phone="+10000000001",
                hashed_password=get_password_hash("admin"),
                role_id=1,
            ),
            User(
                username="barberuser",
                phone="+10000000002",
                hashed_password=get_password_hash("barber123#"),
                role_id=2,
            ),
            User(
                username="testuser",
                phone="+10000000003",
                hashed_password=get_password_hash("testuser1#"),
                role_id=3,
            ),
        ]
        session.add_all(users)
        await session.flush()

        session.add(
            Barber(user_id=users[2].id, full_name="Test Barber", avatar_url=None)
        )
        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session_with_rollback():
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            async_session = async_sessionmaker(
                bind=connection, class_=AsyncSession, expire_on_commit=False
            )
            async with async_session() as session:
                yield session
            await transaction.rollback()


async def fake_rate_limiter():
    yield


@pytest_asyncio.fixture(scope="function")
async def client(db_session_with_rollback):
    app.dependency_overrides[get_session] = lambda: db_session_with_rollback
    app.dependency_overrides[get_login_rate_limiter] = fake_rate_limiter

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


async def get_authorized_client(username: str, password: str, db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_login_rate_limiter] = fake_rate_limiter

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/users/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        ac.headers.update({"Authorization": f"Bearer {token}"})
        yield ac


@pytest_asyncio.fixture(scope="function")
async def authorized_client(db_session_with_rollback):
    async for ac in get_authorized_client(
        "testuser", "testuser1#", db_session_with_rollback
    ):
        yield ac


@pytest_asyncio.fixture(scope="function")
async def barber_client(db_session_with_rollback):
    async for ac in get_authorized_client(
        "barberuser", "barber123#", db_session_with_rollback
    ):
        yield ac


@pytest_asyncio.fixture(scope="function")
async def admin_client(db_session_with_rollback):
    async for ac in get_authorized_client("admin", "admin", db_session_with_rollback):
        yield ac


@pytest_asyncio.fixture(scope="function")
async def super_admin_client(db_session_with_rollback):
    async for ac in get_authorized_client(
        settings.SUPERADMIN_LOGIN,
        settings.SUPERADMIN_PASSWORD,
        db_session_with_rollback,
    ):
        yield ac

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_session
from app.api.routes.users import get_login_rate_limiter
from app.core.config import settings
from app.db.base import Base
from app.main import app

TEST_DATABASE_URL = settings.TEST_DATABASE_URL
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def override_db_session():
    async with TestingSessionLocal() as session:
        yield session


async def fake_rate_limiter():
    yield


@pytest_asyncio.fixture(scope="function")
async def client(override_db_session):
    async def override_get_session():
        yield override_db_session

    app.dependency_overrides[get_session] = override_get_session

    app.dependency_overrides[get_login_rate_limiter] = fake_rate_limiter

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
@pytest_asyncio.fixture(scope="function")
async def authorized_client(client):
    login_response = await client.post(
        "/users/login",
        data={"username": "testuser", "password": "testuser1#"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200, login_response.text
    token_data = login_response.json()
    assert "access_token" in token_data

    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token_data['access_token']}",
    }
    return client


@pytest.mark.asyncio
@pytest_asyncio.fixture(scope="function")
async def admin_client(client):
    login_response = await client.post(
        "/users/login",
        data={
            "username": settings.SUPERADMIN_LOGIN,
            "password": settings.SUPERADMIN_PASSWORD,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200, login_response.text
    token_data = login_response.json()
    assert "access_token" in token_data

    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token_data['access_token']}",
    }
    return client

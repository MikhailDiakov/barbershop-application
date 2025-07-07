import json
from unittest.mock import AsyncMock, patch

import pytest

from app.utils.redis_client import (
    can_request_code,
    delete_barber_rating,
    delete_verification_code,
    get_barber_rating,
    get_verification_code,
    load_barbershop_info_from_redis,
    save_barber_rating,
    save_barbershop_info_to_redis,
    save_verification_code,
)


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_save_verification_code(mock_redis_client):
    mock_redis_client.set = AsyncMock()

    await save_verification_code("+1234567890", "123456", expire_seconds=900)

    mock_redis_client.set.assert_awaited_once_with(
        "password_reset:+1234567890", "123456", ex=900
    )


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_get_verification_code_found(mock_redis_client):
    mock_redis_client.get = AsyncMock(return_value="123456")

    code = await get_verification_code("+1234567890")

    assert code == "123456"
    mock_redis_client.get.assert_awaited_once_with("password_reset:+1234567890")


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_get_verification_code_not_found(mock_redis_client):
    mock_redis_client.get = AsyncMock(return_value=None)

    code = await get_verification_code("+1234567890")

    assert code is None
    mock_redis_client.get.assert_awaited_once_with("password_reset:+1234567890")


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_delete_verification_code(mock_redis_client):
    mock_redis_client.delete = AsyncMock()

    await delete_verification_code("+1234567890")

    mock_redis_client.delete.assert_awaited_once_with("password_reset:+1234567890")


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_can_request_code_rate_limit_active(mock_redis_client):
    mock_redis_client.exists = AsyncMock(return_value=1)
    mock_redis_client.set = AsyncMock()

    result = await can_request_code("+1234567890", limit_seconds=60)

    assert result is False
    mock_redis_client.exists.assert_awaited_once_with(
        "password_reset_rate_limit:+1234567890"
    )
    mock_redis_client.set.assert_not_called()


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_can_request_code_rate_limit_not_active(mock_redis_client):
    mock_redis_client.exists = AsyncMock(return_value=0)
    mock_redis_client.set = AsyncMock()

    result = await can_request_code("+1234567890", limit_seconds=60)

    assert result is True
    mock_redis_client.exists.assert_awaited_once_with(
        "password_reset_rate_limit:+1234567890"
    )
    mock_redis_client.set.assert_awaited_once_with(
        "password_reset_rate_limit:+1234567890", "1", ex=60
    )


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_save_barber_rating(mock_redis_client):
    mock_redis_client.set = AsyncMock()

    await save_barber_rating(42, 4.5, 10, expire_seconds=86400)

    mock_redis_client.set.assert_awaited_once_with(
        "barber_rating:42", "4.5:10", ex=86400
    )


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_get_barber_rating_found(mock_redis_client):
    mock_redis_client.get = AsyncMock(return_value="4.5:10")
    mock_redis_client.expire = AsyncMock()

    rating = await get_barber_rating(42)

    assert rating == (4.5, 10)
    mock_redis_client.get.assert_awaited_once_with("barber_rating:42")
    mock_redis_client.expire.assert_awaited_once_with("barber_rating:42", 86400)


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_get_barber_rating_not_found(mock_redis_client):
    mock_redis_client.get = AsyncMock(return_value=None)

    rating = await get_barber_rating(42)

    assert rating is None
    mock_redis_client.get.assert_awaited_once_with("barber_rating:42")


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_delete_barber_rating(mock_redis_client):
    mock_redis_client.delete = AsyncMock()

    await delete_barber_rating(42)

    mock_redis_client.delete.assert_awaited_once_with("barber_rating:42")


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_load_barbershop_info_from_redis_found(mock_redis_client):
    sample_data = {"name": "Barbershop"}
    mock_redis_client.get = AsyncMock(return_value=json.dumps(sample_data))

    data = await load_barbershop_info_from_redis()

    assert data == sample_data
    mock_redis_client.get.assert_awaited_once_with("barbershop_info")


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_load_barbershop_info_from_redis_not_found(mock_redis_client):
    mock_redis_client.get = AsyncMock(return_value=None)

    data = await load_barbershop_info_from_redis()

    assert data is None
    mock_redis_client.get.assert_awaited_once_with("barbershop_info")


@pytest.mark.asyncio
@patch("app.utils.redis_client.redis_client")
async def test_save_barbershop_info_to_redis(mock_redis_client):
    mock_redis_client.set = AsyncMock()

    data = {"name": "Barbershop"}
    await save_barbershop_info_to_redis(data)

    mock_redis_client.set.assert_awaited_once_with(
        "barbershop_info", json.dumps(data), ex=3600
    )

import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def save_verification_code(phone: str, code: str, expire_seconds: int = 900):
    key = f"password_reset:{phone}"
    await redis_client.set(key, code, ex=expire_seconds)


async def get_verification_code(phone: str) -> str | None:
    key = f"password_reset:{phone}"
    return await redis_client.get(key)


async def delete_verification_code(phone: str):
    key = f"password_reset:{phone}"
    await redis_client.delete(key)


async def can_request_code(phone: str, limit_seconds: int = 60) -> bool:
    key = f"password_reset_rate_limit:{phone}"
    exists = await redis_client.exists(key)
    if exists:
        return False
    await redis_client.set(key, "1", ex=limit_seconds)
    return True


BARBER_RATING_EXPIRE = 86400


async def save_barber_rating(
    barber_id: int,
    avg_rating: float,
    count: int,
    expire_seconds: int = BARBER_RATING_EXPIRE,
):
    key = f"barber_rating:{barber_id}"
    value = f"{avg_rating}:{count}"
    await redis_client.set(key, value, ex=expire_seconds)


async def get_barber_rating(barber_id: int) -> tuple[float, int] | None:
    key = f"barber_rating:{barber_id}"
    value = await redis_client.get(key)
    if not value:
        return None

    await redis_client.expire(key, BARBER_RATING_EXPIRE)

    avg_rating_str, count_str = value.split(":")
    return float(avg_rating_str), int(count_str)


async def delete_barber_rating(barber_id: int):
    key = f"barber_rating:{barber_id}"
    await redis_client.delete(key)

import redis.asyncio as redis

from app.core.config import settings
from app.utils.logger import logger

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def save_verification_code(phone: str, code: str, expire_seconds: int = 900):
    key = f"password_reset:{phone}"
    await redis_client.set(key, code, ex=expire_seconds)
    logger.info(
        f"Saved verification code for phone={phone} with expiry={expire_seconds}s"
    )


async def get_verification_code(phone: str) -> str | None:
    key = f"password_reset:{phone}"
    code = await redis_client.get(key)
    if code:
        logger.debug(f"Verification code retrieved for phone={phone}")
    else:
        logger.debug(f"No verification code found for phone={phone}")
    return code


async def delete_verification_code(phone: str):
    key = f"password_reset:{phone}"
    await redis_client.delete(key)
    logger.info(f"Deleted verification code for phone={phone}")


async def can_request_code(phone: str, limit_seconds: int = 60) -> bool:
    key = f"password_reset_rate_limit:{phone}"
    exists = await redis_client.exists(key)
    if exists:
        logger.info(f"Rate limit active: cannot request new code for phone={phone}")
        return False
    await redis_client.set(key, "1", ex=limit_seconds)
    logger.info(f"Rate limit set for phone={phone} with duration={limit_seconds}s")
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
    logger.info(
        f"Saved barber rating for barber_id={barber_id}: avg_rating={avg_rating}, count={count}, expiry={expire_seconds}s"
    )


async def get_barber_rating(barber_id: int) -> tuple[float, int] | None:
    key = f"barber_rating:{barber_id}"
    value = await redis_client.get(key)
    if not value:
        logger.debug(f"No cached rating found for barber_id={barber_id}")
        return None

    await redis_client.expire(key, BARBER_RATING_EXPIRE)
    logger.debug(f"Refreshed expiry for barber rating cache barber_id={barber_id}")

    avg_rating_str, count_str = value.split(":")
    return float(avg_rating_str), int(count_str)


async def delete_barber_rating(barber_id: int):
    key = f"barber_rating:{barber_id}"
    await redis_client.delete(key)
    logger.info(f"Deleted cached barber rating for barber_id={barber_id}")

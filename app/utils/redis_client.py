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

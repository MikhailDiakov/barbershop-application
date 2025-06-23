from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logger import logger
from app.utils.redis_client import get_barber_rating, save_barber_rating
from app.utils.selectors.reviews import get_barber_rating_from_db


async def get_rating_for_barber(db: AsyncSession, barber_id: int) -> tuple[float, int]:
    cached = await get_barber_rating(barber_id)
    if cached:
        logger.info("Cache hit for barber rating", extra={"barber_id": barber_id})
        return cached

    logger.info("Cache miss for barber rating", extra={"barber_id": barber_id})
    avg, count = await get_barber_rating_from_db(db, barber_id)
    await save_barber_rating(barber_id, avg, count)
    return avg, count

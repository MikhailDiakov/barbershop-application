from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.review import Review


async def get_all_reviews(
    db: AsyncSession, only_unapproved: bool = False
) -> list[Review]:
    query = select(Review).options(joinedload(Review.client), joinedload(Review.barber))
    if only_unapproved:
        query = query.where(Review.is_approved.is_(False))

    result = await db.execute(query)
    return result.scalars().all()


async def get_barber_rating_from_db(
    db: AsyncSession, barber_id: int
) -> tuple[float, int]:
    result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.barber_id == barber_id,
            Review.is_approved.is_(True),
        )
    )
    avg_rating, count = result.one()
    return avg_rating or 0.0, count or 0

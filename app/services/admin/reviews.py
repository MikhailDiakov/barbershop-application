from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.services.admin.utils import ensure_admin
from app.utils.redis_client import get_barber_rating, save_barber_rating
from app.utils.selectors.reviews import get_all_reviews, get_barber_rating_from_db


async def get_all_reviews_service(
    db: AsyncSession, user_role: str, only_unapproved: bool = False
):
    ensure_admin(user_role)
    return await get_all_reviews(db, only_unapproved=only_unapproved)


async def approve_review_service(db: AsyncSession, review_id: int, user_role: str):
    ensure_admin(user_role)

    review = await db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.is_approved:
        raise HTTPException(status_code=400, detail="Review already approved")

    review.is_approved = True
    await db.commit()

    cached_rating = await get_barber_rating(review.barber_id)

    if cached_rating:
        avg_rating, count = cached_rating
        total_sum = avg_rating * count + review.rating
        new_count = count + 1
        new_avg = total_sum / new_count
    else:
        new_avg, new_count = await get_barber_rating_from_db(db, review.barber_id)

    await save_barber_rating(
        barber_id=review.barber_id,
        avg_rating=new_avg,
        count=new_count,
    )

    return review


async def delete_review_service(db: AsyncSession, review_id: int, user_role: str):
    ensure_admin(user_role)
    review = await db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    barber_id = review.barber_id
    was_approved = review.is_approved
    removed_rating = review.rating

    await db.delete(review)
    await db.commit()

    if not was_approved:
        return {"detail": "Review deleted"}

    cached = await get_barber_rating(barber_id)

    if cached:
        avg_rating, count = cached
        if count > 1:
            avg_rating = (avg_rating * count - removed_rating) / (count - 1)
            count -= 1
        else:
            avg_rating = 0
            count = 0
    else:
        avg_rating, count = await get_barber_rating_from_db(db, barber_id)

    await save_barber_rating(barber_id=barber_id, avg_rating=avg_rating, count=count)
    return {"detail": "Review deleted"}

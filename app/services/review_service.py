from typing import List

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.review import Review
from app.schemas.review import ReviewCreate
from app.utils.selectors.barber import get_barber_by_id


async def create_review_service(
    db: AsyncSession,
    review_in: ReviewCreate,
    current_user: dict,
) -> Review:
    barber = await get_barber_by_id(db, review_in.barber_id)
    if barber is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Barber not found"
        )
    new_review = Review(
        client_id=int(current_user["id"]),
        barber_id=review_in.barber_id,
        rating=review_in.rating,
        comment=review_in.comment,
        is_approved=False,
    )

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    return new_review


async def get_reviews_by_user_service(
    db: AsyncSession,
    user_id: int | str,
    skip: int = 0,
    limit: int = 10,
) -> List[Review]:
    stmt = (
        select(Review)
        .where(Review.client_id == int(user_id))
        .order_by(desc(Review.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

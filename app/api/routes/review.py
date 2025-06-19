from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_session
from app.schemas.review import ReviewCreate, ReviewRead
from app.services.review_service import (
    create_review_service,
    get_reviews_by_user_service,
)

router = APIRouter()


@router.post("/", response_model=ReviewRead)
async def create_review(
    review_in: ReviewCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    review = await create_review_service(db, review_in, current_user)
    return review


@router.get("/my-reviews/", response_model=List[ReviewRead])
async def get_my_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    reviews = await get_reviews_by_user_service(db, current_user["id"], skip, limit)
    return reviews

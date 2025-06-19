from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_session
from app.schemas.review import ReviewAdminRead
from app.services.admin.reviews import (
    approve_review_service,
    delete_review_service,
    get_all_reviews_service,
)

router = APIRouter()


@router.get("/", response_model=list[ReviewAdminRead])
async def list_reviews(
    only_unapproved: bool = False,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_all_reviews_service(
        db=db, user_role=current_user["role"], only_unapproved=only_unapproved
    )


@router.post("/{review_id}/approve", response_model=ReviewAdminRead)
async def approve_review(
    review_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await approve_review_service(db, review_id, current_user["role"])


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await delete_review_service(db, review_id, current_user["role"])
    return {"detail": "Review deleted"}

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_session
from app.schemas.user import PromoteUserToBarberRequest, UserRead, UserUpdateForAdmin
from app.services.admin.users import (
    delete_user,
    get_users,
    promote_user_to_barber,
    update_user,
)
from app.utils.selectors.user import get_user_by_id

router = APIRouter()


@router.get("/", response_model=list[UserRead])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    username: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_users(
        db,
        current_user["role"],
        admin_id=current_user["id"],
        skip=skip,
        limit=limit,
        username_filter=username,
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_user_by_id(
        db,
        user_id,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.put("/{user_id}", response_model=UserRead)
async def update_user_data(
    user_id: int,
    data: UserUpdateForAdmin,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await update_user(
        db,
        user_id,
        data.dict(exclude_unset=True),
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_route(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await delete_user(
        db,
        user_id,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.post(
    "/{user_id}/promote-to-barber",
    response_model=UserRead,
    response_model_exclude_none=True,
)
async def promote_user_to_barber_route(
    user_id: int,
    data: PromoteUserToBarberRequest,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    updated_user = await promote_user_to_barber(
        db,
        user_id,
        current_user["role"],
        data.full_name,
        admin_id=current_user["id"],
    )
    return updated_user

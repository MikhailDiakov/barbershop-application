from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_session
from app.schemas.user import AdminOut, UserRead
from app.services.admin.superadmin import (
    demote_admin_to_client,
    get_admin_by_id,
    get_all_admins,
    promote_user_to_admin,
    raise_fake_error,
)

router = APIRouter()


@router.get("/admins", response_model=list[AdminOut])
async def list_admins(
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_all_admins(
        db,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.get("/admins/{admin_id}", response_model=AdminOut)
async def get_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_admin_by_id(
        db,
        admin_id,
        current_user["role"],
        admin_id=current_user["id"],
    )


@router.post("/users/{user_id}/promote", response_model=UserRead)
async def promote_to_admin_route(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    user = await promote_user_to_admin(
        db=db,
        target_user_id=user_id,
        current_user_id=current_user["id"],
        current_user_role=current_user["role"],
    )
    return user


@router.post("/users/{user_id}/demote", response_model=UserRead)
async def demote_from_admin_route(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    user = await demote_admin_to_client(
        db=db,
        target_user_id=user_id,
        current_user_id=current_user["id"],
        current_user_role=current_user["role"],
    )
    return user


@router.get("/debug-error")
async def debug_error_route(
    error_type: str = Query(default="zero_division"),
    current_user=Depends(get_current_user_info),
):
    """
    Trigger a debug error to test Sentry. Only for superadmin.
    error_type options: zero_division | runtime | http_403 | custom
    """
    raise_fake_error(current_user_role=current_user["role"], error_type=error_type)

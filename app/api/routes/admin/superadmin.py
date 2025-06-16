from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.security import get_current_user_info
from app.schemas.user import AdminOut, UserReadwithoutProfile
from app.services.admin.superadmin import (
    demote_admin_to_client,
    get_admin_by_id,
    get_all_admins,
    promote_user_to_admin,
)

router = APIRouter()


@router.get("/admins", response_model=list[AdminOut])
async def list_admins(
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_all_admins(db, current_user["role"])


@router.get("/admins/{admin_id}", response_model=AdminOut)
async def get_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_admin_by_id(db, admin_id, current_user["role"])


@router.post("/users/{user_id}/promote", response_model=UserReadwithoutProfile)
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


@router.post("/users/{user_id}/demote", response_model=UserReadwithoutProfile)
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

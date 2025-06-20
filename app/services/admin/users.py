from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hash import get_password_hash
from app.models import User
from app.models.barber import Barber
from app.models.enums import RoleEnum
from app.services.admin.utils import ensure_admin
from app.utils.selectors.barber import get_barber_by_user_id
from app.utils.selectors.user import (
    get_user_by_id,
    get_user_by_phone,
    get_user_by_username,
)


async def get_users(
    db: AsyncSession,
    user_role: str,
    skip: int = 0,
    limit: int = 10,
    username_filter: Optional[str] = None,
):
    ensure_admin(user_role)

    query = select(User)

    if username_filter:
        query = query.where(User.username.ilike(f"%{username_filter}%"))

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()
    return users


async def update_user(db: AsyncSession, user_id: int, data: dict, user_role: str):
    ensure_admin(user_role)

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    target_role = user.role_id
    current_role = int(user_role)

    if current_role == RoleEnum.ADMIN.value:
        if target_role in (RoleEnum.ADMIN.value, RoleEnum.SUPERADMIN.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot modify Admin or SuperAdmin users",
            )
    elif current_role == RoleEnum.SUPERADMIN.value:
        if target_role == RoleEnum.SUPERADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot modify another SuperAdmin",
            )

    if "username" in data:
        existing = await get_user_by_username(db, data["username"])
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    if "phone" in data:
        existing = await get_user_by_phone(db, data["phone"])
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists",
            )

    if "password" in data:
        data["hashed_password"] = get_password_hash(data.pop("password"))

    for key, value in data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int, user_role: str):
    ensure_admin(user_role)

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role_id in (RoleEnum.SUPERADMIN.value, RoleEnum.ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete Admin or SuperAdmin users",
        )
    if user.role_id == RoleEnum.BARBER.value:
        barber = await get_barber_by_user_id(db, user_id)
        if barber:
            await db.delete(barber)

    await db.delete(user)
    await db.commit()


async def promote_user_to_barber(
    db: AsyncSession, user_id: int, user_role: str, full_name: str
):
    ensure_admin(user_role)

    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.role_id in (RoleEnum.ADMIN.value, RoleEnum.SUPERADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot promote Admin or SuperAdmin users to Barber",
        )

    if user.role_id == RoleEnum.BARBER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a barber"
        )

    user.role_id = RoleEnum.BARBER.value
    db.add(user)
    await db.flush()

    barber = Barber(user_id=user.id, full_name=full_name, avatar_url=None)
    db.add(barber)
    await db.commit()
    await db.refresh(user)

    return user

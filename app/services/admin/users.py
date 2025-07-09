from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hash import get_password_hash
from app.models import User
from app.models.barber import Barber
from app.models.enums import RoleEnum
from app.services.admin.utils import ensure_admin
from app.utils.logger import logger
from app.utils.selectors.barber import get_barber_by_user_id
from app.utils.selectors.user import (
    get_user_by_id,
    get_user_by_phone,
    get_user_by_username,
)


async def get_users(
    db: AsyncSession,
    user_role: str,
    admin_id: int,
    skip: int = 0,
    limit: int = 10,
    username_filter: Optional[str] = None,
):
    ensure_admin(user_role)
    logger.info(
        "Fetching users",
        extra={
            "role": user_role,
            "admin_id": admin_id,
            "skip": skip,
            "limit": limit,
            "username_filter": username_filter,
        },
    )

    query = select(User)
    if username_filter:
        query = query.where(User.username.ilike(f"%{username_filter}%"))
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    logger.info(
        "Users fetched",
        extra={
            "action": "get_users",
            "admin_id": admin_id,
            "count": len(users),
        },
    )
    return users


async def get_user_by_id_for_admin(
    db: AsyncSession,
    user_id: int,
    user_role: str,
    admin_id: int,
) -> User:
    ensure_admin(user_role)

    logger.info(
        "Fetching user by ID",
        extra={
            "role": user_role,
            "admin_id": admin_id,
            "target_user_id": user_id,
        },
    )

    user = await get_user_by_id(db, user_id)

    if not user:
        logger.warning(
            "User not found",
            extra={"admin_id": admin_id, "user_id": user_id},
        )
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(
        "User fetched",
        extra={"admin_id": admin_id, "user_id": user.id},
    )
    return user


async def update_user(
    db: AsyncSession,
    user_id: int,
    data: dict,
    user_role: str,
    admin_id: int,
):
    ensure_admin(user_role)
    logger.info(
        "Attempting to update user",
        extra={
            "admin_id": admin_id,
            "admin_role": user_role,
            "target_user_id": user_id,
            "fields": list(data.keys()),
        },
    )

    user = await get_user_by_id(db, user_id)
    if not user:
        logger.warning(
            "User not found for update",
            extra={"admin_id": admin_id, "user_id": user_id},
        )
        raise HTTPException(status_code=404, detail="User not found")

    if int(user_role) == RoleEnum.ADMIN.value and user.role_id in (
        RoleEnum.ADMIN.value,
        RoleEnum.SUPERADMIN.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot modify Admin or SuperAdmin users",
        )
    if (
        int(user_role) == RoleEnum.SUPERADMIN.value
        and user.role_id == RoleEnum.SUPERADMIN.value
    ):
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

    logger.info(
        "User updated",
        extra={"admin_id": admin_id, "user_id": user.id},
    )
    return user


async def delete_user(
    db: AsyncSession,
    user_id: int,
    user_role: str,
    admin_id: int,
):
    ensure_admin(user_role)
    logger.info(
        "Attempting to delete user",
        extra={"admin_id": admin_id, "user_id": user_id, "admin_role": user_role},
    )

    user = await get_user_by_id(db, user_id)
    if not user:
        logger.warning(
            "User not found for deletion",
            extra={"admin_id": admin_id, "user_id": user_id},
        )
        raise HTTPException(status_code=404, detail="User not found")

    if user.role_id in (RoleEnum.SUPERADMIN.value, RoleEnum.ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete Admin or SuperAdmin users",
        )

    if user.role_id == RoleEnum.BARBER.value:
        barber = await get_barber_by_user_id(db, user_id)
        if barber:
            logger.info(
                "Deleting associated barber",
                extra={"admin_id": admin_id, "barber_id": barber.id},
            )
            await db.delete(barber)

    await db.delete(user)
    await db.commit()
    logger.info("User deleted", extra={"admin_id": admin_id, "user_id": user_id})


async def promote_user_to_barber(
    db: AsyncSession,
    user_id: int,
    user_role: str,
    full_name: str,
    admin_id: int,
):
    ensure_admin(user_role)
    logger.info(
        "Attempting to promote user to barber",
        extra={"admin_id": admin_id, "user_id": user_id, "admin_role": user_role},
    )

    user = await get_user_by_id(db, user_id)
    if not user:
        logger.warning(
            "User not found for promotion",
            extra={"admin_id": admin_id, "user_id": user_id},
        )
        raise HTTPException(status_code=404, detail="User not found")

    if user.role_id in (RoleEnum.ADMIN.value, RoleEnum.SUPERADMIN.value):
        raise HTTPException(403, "Cannot promote Admin or SuperAdmin users to Barber")

    if user.role_id == RoleEnum.BARBER.value:
        raise HTTPException(400, "User is already a barber")

    user.role_id = RoleEnum.BARBER.value
    db.add(user)
    await db.flush()

    barber = Barber(user_id=user.id, full_name=full_name, avatar_url=None)
    db.add(barber)
    await db.commit()
    await db.refresh(user)

    logger.info(
        "User promoted to barber",
        extra={"admin_id": admin_id, "user_id": user.id, "barber_id": barber.id},
    )
    return user

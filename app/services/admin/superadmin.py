from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.enums import RoleEnum
from app.services.admin.utils import ensure_superadmin
from app.utils.logger import logger
from app.utils.selectors.user import get_user_by_id


async def get_all_admins(db: AsyncSession, current_user_role: str) -> list[User]:
    ensure_superadmin(current_user_role)
    logger.info("Fetching all admins", extra={"role": current_user_role})

    result = await db.execute(
        select(User).where(
            User.role_id.in_([RoleEnum.ADMIN.value, RoleEnum.SUPERADMIN.value])
        )
    )
    admins = result.scalars().all()
    logger.info("Fetched all admins", extra={"count": len(admins)})
    return admins


async def get_admin_by_id(
    db: AsyncSession, admin_id: int, current_user_role: str
) -> User:
    ensure_superadmin(current_user_role)
    logger.info("Fetching admin by ID", extra={"admin_id": admin_id})

    result = await db.execute(
        select(User).where(
            User.id == admin_id,
            User.role_id.in_([RoleEnum.ADMIN.value, RoleEnum.SUPERADMIN.value]),
        )
    )
    admin = result.scalars().first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found"
        )

    logger.info("Admin fetched", extra={"admin_id": admin.id})
    return admin


async def promote_user_to_admin(
    db: AsyncSession, target_user_id: int, current_user_id: int, current_user_role: int
) -> User:
    ensure_superadmin(current_user_role)
    logger.info(
        "Promote user to admin requested",
        extra={
            "target_user_id": target_user_id,
            "by_user_id": current_user_id,
        },
    )

    if target_user_id == current_user_id:
        logger.warning(
            "Attempt to self-promote blocked", extra={"user_id": current_user_id}
        )
        raise HTTPException(400, detail="You cannot promote yourself")

    user = await get_user_by_id(db, target_user_id)

    if not user:
        logger.warning("User to promote not found", extra={"user_id": target_user_id})
        raise HTTPException(404, detail="User not found")

    if user.role_id == RoleEnum.SUPERADMIN:
        logger.warning(
            "Attempt to promote superadmin", extra={"user_id": target_user_id}
        )
        raise HTTPException(403, detail="Cannot promote another superadmin")

    if user.role_id == RoleEnum.BARBER:
        logger.warning(
            "Attempt to promote barber to admin", extra={"user_id": target_user_id}
        )
        raise HTTPException(400, detail="Cannot promote a barber to admin")

    if user.role_id == RoleEnum.ADMIN:
        logger.warning("User already an admin", extra={"user_id": target_user_id})
        raise HTTPException(400, detail="User is already an admin")

    user.role_id = RoleEnum.ADMIN
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("User promoted to admin", extra={"user_id": user.id})
    return user


async def demote_admin_to_client(
    db: AsyncSession, target_user_id: int, current_user_id: int, current_user_role: int
) -> User:
    ensure_superadmin(current_user_role)
    logger.info(
        "Demotion of admin to client requested",
        extra={
            "target_user_id": target_user_id,
            "by_user_id": current_user_id,
        },
    )

    if target_user_id == current_user_id:
        logger.warning(
            "Attempt to self-demote blocked", extra={"user_id": current_user_id}
        )
        raise HTTPException(400, detail="You cannot demote yourself")

    user = await get_user_by_id(db, target_user_id)

    if not user:
        logger.warning("User to demote not found", extra={"user_id": target_user_id})
        raise HTTPException(404, detail="User not found")

    if user.role_id != RoleEnum.ADMIN:
        logger.warning("User is not an admin", extra={"user_id": target_user_id})
        raise HTTPException(400, detail="User is not an admin")

    user.role_id = RoleEnum.CLIENT
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("User demoted to client", extra={"user_id": user.id})
    return user


def raise_fake_error(current_user_role: int, error_type: str = "zero_division") -> None:
    ensure_superadmin(current_user_role)
    logger.info("Raising fake error for Sentry test", extra={"error_type": error_type})

    if error_type == "zero_division":
        _ = 1 / 0
    elif error_type == "runtime":
        raise RuntimeError("This is a test RuntimeError for Sentry.")
    elif error_type == "http_403":
        raise HTTPException(status_code=403, detail="Access denied.")
    elif error_type == "custom":
        raise Exception("Custom generic exception for Sentry test.")
    else:
        logger.error("Unsupported error type", extra={"error_type": error_type})
        raise ValueError("Unsupported error type.")

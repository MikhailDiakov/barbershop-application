from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.enums import RoleEnum
from app.services.admin.utils import ensure_superadmin
from app.utils.selectors.user import get_user_by_id


async def get_all_admins(db: AsyncSession, current_user_role: str) -> list[User]:
    ensure_superadmin(current_user_role)

    result = await db.execute(
        select(User).where(
            User.role_id.in_([RoleEnum.ADMIN.value, RoleEnum.SUPERADMIN.value])
        )
    )
    admins = result.scalars().all()
    return admins


async def get_admin_by_id(
    db: AsyncSession, admin_id: int, current_user_role: str
) -> User:
    ensure_superadmin(current_user_role)

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
    return admin


async def promote_user_to_admin(
    db: AsyncSession, target_user_id: int, current_user_id: int, current_user_role: int
) -> User:
    ensure_superadmin(current_user_role)

    if target_user_id == current_user_id:
        raise HTTPException(400, detail="You cannot promote yourself")

    user = await get_user_by_id(db, target_user_id)

    if not user:
        raise HTTPException(404, detail="User not found")

    if user.role_id == RoleEnum.SUPERADMIN:
        raise HTTPException(403, detail="Cannot promote another superadmin")

    if user.role_id == RoleEnum.BARBER:
        raise HTTPException(400, detail="Cannot promote a barber to admin")

    if user.role_id == RoleEnum.ADMIN:
        raise HTTPException(400, detail="User is already an admin")

    user.role_id = RoleEnum.ADMIN
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def demote_admin_to_client(
    db: AsyncSession, target_user_id: int, current_user_id: int, current_user_role: int
) -> User:
    ensure_superadmin(current_user_role)

    if target_user_id == current_user_id:
        raise HTTPException(400, detail="You cannot demote yourself")

    user = await get_user_by_id(db, target_user_id)

    if not user:
        raise HTTPException(404, detail="User not found")

    if user.role_id != RoleEnum.ADMIN:
        raise HTTPException(400, detail="User is not an admin")

    user.role_id = RoleEnum.CLIENT
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

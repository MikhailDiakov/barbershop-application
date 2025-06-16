from fastapi import HTTPException, status

from app.models.enums import RoleEnum


def ensure_admin(role: str):
    if int(role) not in (RoleEnum.ADMIN.value, RoleEnum.SUPERADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: only admins can perform this action",
        )


def ensure_superadmin(role: str):
    if int(role) != RoleEnum.SUPERADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: only superadmins can perform this action",
        )

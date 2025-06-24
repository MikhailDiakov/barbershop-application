from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hash import get_password_hash, verify_password
from app.models.user import User
from app.utils.celery_tasks.sms import send_sms_task
from app.utils.code_generator import generate_verification_code
from app.utils.logger import logger
from app.utils.redis_client import (
    can_request_code,
    delete_verification_code,
    get_verification_code,
    save_verification_code,
)
from app.utils.selectors.user import (
    get_user_by_id,
    get_user_by_phone,
    get_user_by_username,
)


async def create_user(
    db: AsyncSession, username: str, phone: str, password: str, role_id: int = 3
) -> User:
    existing_user = await get_user_by_username(db, username)
    if existing_user:
        logger.warning(
            "User creation failed: username already exists",
            extra={"action": "create_user", "username": username},
        )
        raise HTTPException(status_code=400, detail="Username already registered")

    existing_phone = await get_user_by_phone(db, phone)
    if existing_phone:
        logger.warning(
            "User creation failed: phone already exists",
            extra={"action": "create_user", "phone": phone},
        )
        raise HTTPException(status_code=400, detail="Phone number already registered")

    hashed_password = get_password_hash(password)
    user = User(
        username=username, phone=phone, hashed_password=hashed_password, role_id=role_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(
        "User created",
        extra={
            "action": "create_user",
            "username": username,
            "phone": phone,
            "role_id": role_id,
            "user_id": user.id,
        },
    )

    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(
            "Login failed: invalid credentials",
            extra={"action": "login", "username": username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    logger.info(
        "User authenticated successfully",
        extra={"action": "login", "username": username, "user_id": user.id},
    )
    return user


async def get_user_profile(db: AsyncSession, user_id: int) -> User:
    user = await get_user_by_id(db, user_id)
    if user is None:
        logger.warning(
            "User profile fetch failed: user not found",
            extra={"action": "get_user_profile", "user_id": user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    logger.info(
        "User profile fetched successfully",
        extra={"action": "get_user_profile", "user_id": user_id},
    )
    return user


async def update_user_profile(
    db: AsyncSession,
    user_id: int,
    phone: Optional[str] = None,
    old_password: Optional[str] = None,
    new_password: Optional[str] = None,
    confirm_password: Optional[str] = None,
):
    user = await get_user_by_id(db, user_id)
    if not user:
        logger.warning(
            "User profile update failed: user not found",
            extra={"action": "update_profile", "user_id": user_id},
        )
        raise HTTPException(status_code=404, detail="User not found")

    if phone:
        existing = await get_user_by_phone(db, phone)
        if existing and existing.id != user_id:
            logger.warning(
                "User profile update failed: phone already in use",
                extra={"action": "update_profile", "user_id": user_id, "phone": phone},
            )
            raise HTTPException(status_code=400, detail="Phone already in use")
        if not old_password or not verify_password(old_password, user.hashed_password):
            logger.warning(
                "User profile update failed: password required to change phone",
                extra={"action": "update_profile", "user_id": user_id, "phone": phone},
            )
            raise HTTPException(
                status_code=400, detail="Password required to change phone"
            )
        user.phone = phone
        logger.info(
            "User phone updated",
            extra={"action": "update_profile", "user_id": user_id, "new_phone": phone},
        )

    if new_password:
        if not old_password or not verify_password(old_password, user.hashed_password):
            logger.warning(
                "User profile update failed: old password incorrect",
                extra={"action": "update_profile", "user_id": user_id},
            )
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        user.hashed_password = get_password_hash(new_password)
        logger.info(
            "User password updated",
            extra={"action": "update_profile", "user_id": user_id},
        )

    await db.commit()
    await db.refresh(user)

    logger.info(
        "User profile updated successfully",
        extra={"action": "update_profile", "user_id": user_id},
    )

    return user


async def send_password_reset_code(db: AsyncSession, phone: str):
    user = await get_user_by_phone(db, phone)
    if not user:
        logger.warning(
            "Password reset code request failed: user not found",
            extra={"action": "send_reset_code", "phone": phone},
        )
        return
    can_request = await can_request_code(phone)
    if not can_request:
        logger.warning(
            "Password reset code request throttled: too many requests",
            extra={"action": "send_reset_code", "phone": phone},
        )
        raise HTTPException(
            status_code=429, detail="Too many requests, please wait before retrying."
        )
    code = generate_verification_code()
    await save_verification_code(phone=phone, code=code)
    send_sms_task.delay(
        phone,
        f"Your reset code is: {code}. The code will become invalid in 15 minutes.",
    )
    logger.info(
        "Password reset code sent", extra={"action": "send_reset_code", "phone": phone}
    )


async def confirm_password_reset(
    db: AsyncSession, phone: str, code: str, new_password: str
) -> User:
    user = await get_user_by_phone(db, phone)
    if not user:
        logger.warning(
            "Password reset confirmation failed: user not found",
            extra={"action": "confirm_reset_code", "phone": phone},
        )

        raise HTTPException(status_code=404, detail="User not found")

    saved_code = await get_verification_code(phone)
    if saved_code != code:
        logger.warning(
            "Password reset confirmation failed: invalid or expired code",
            extra={"action": "confirm_reset_code", "phone": phone},
        )
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    user.hashed_password = get_password_hash(new_password)
    await delete_verification_code(phone)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(
        "Password reset successful",
        extra={"action": "confirm_reset_code", "user_id": user.id, "phone": phone},
    )
    return user

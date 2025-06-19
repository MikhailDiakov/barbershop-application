from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hash import get_password_hash, verify_password
from app.models.user import User
from app.utils.celery_tasks.sms import send_sms_task
from app.utils.code_generator import generate_verification_code
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
        raise HTTPException(status_code=400, detail="Username already registered")
    existing_phone = await get_user_by_phone(db, phone)
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    hashed_password = get_password_hash(password)
    user = User(
        username=username, phone=phone, hashed_password=hashed_password, role_id=role_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
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
        raise HTTPException(status_code=404, detail="User not found")

    if phone:
        existing = await get_user_by_phone(db, phone)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Phone already in use")
        if not old_password or not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Password required to change phone"
            )
        user.phone = phone

    if new_password:
        if not old_password or not verify_password(old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        user.hashed_password = get_password_hash(new_password)

    await db.commit()
    await db.refresh(user)
    return user


async def send_password_reset_code(db: AsyncSession, phone: str):
    user = await get_user_by_phone(db, phone)
    if not user:
        return
    can_request = await can_request_code(phone)
    if not can_request:
        raise HTTPException(
            status_code=429, detail="Too many requests, please wait before retrying."
        )
    code = generate_verification_code()
    await save_verification_code(phone=phone, code=code)
    send_sms_task.delay(
        phone,
        f"Your reset code is: {code}. The code will become invalid in 15 minutes.",
    )


async def confirm_password_reset(
    db: AsyncSession, phone: str, code: str, new_password: str
) -> User:
    user = await get_user_by_phone(db, phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    saved_code = await get_verification_code(phone)
    if saved_code != code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    user.hashed_password = get_password_hash(new_password)
    await delete_verification_code(phone)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

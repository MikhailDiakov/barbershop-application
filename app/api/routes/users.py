from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.security import create_access_token, get_current_user
from app.schemas.token import Token
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    UserCreate,
    UserPasswordUpdate,
    UserPhoneUpdate,
    UserRead,
)
from app.services.user_service import (
    authenticate_user,
    change_user_password,
    change_user_phone,
    confirm_password_reset,
    create_user,
    send_password_reset_code,
)

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    user = await create_user(db, user_in.username, user_in.phone, user_in.password)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    access_token = create_access_token(data={"id": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def get_my_user(
    current_user=Depends(get_current_user),
):
    return current_user


@router.put("/me/change-phone", response_model=UserRead)
async def change_phone(
    phone_update: UserPhoneUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    try:
        user = await change_user_phone(
            db=db,
            user_id=current_user.id,
            new_phone=phone_update.phone,
            password=phone_update.password,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/me/change-password", response_model=UserRead)
async def change_password(
    password_update: UserPasswordUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    try:
        user = await change_user_password(
            db=db,
            user_id=current_user.id,
            old_password=password_update.old_password,
            new_password=password_update.new_password,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/password-reset/request")
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_session),
):
    await send_password_reset_code(db, data.phone)
    return {"detail": "Verification code sent"}


@router.post("/password-reset/confirm", response_model=UserRead)
async def password_reset_confirm(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_session),
):
    user = await confirm_password_reset(
        db=db,
        phone=data.phone,
        code=data.code,
        new_password=data.new_password,
    )
    return user

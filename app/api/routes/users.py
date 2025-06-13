from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.security import create_access_token, get_current_user
from app.schemas.token import Token
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    UserCreate,
    UserProfileUpdate,
    UserRead,
)
from app.services.user_service import (
    authenticate_user,
    confirm_password_reset,
    create_user,
    send_password_reset_code,
    update_user_profile,
)

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    user = await create_user(db, user_in.username, user_in.phone, user_in.password)
    return user


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    access_token = create_access_token(
        data={"id": str(user.id), "role": str(user.role_id)}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead, response_model_exclude_none=True)
async def get_my_user(
    current_user=Depends(get_current_user),
):
    return current_user


@router.put("/me/update", response_model=UserRead)
async def update_my_profile(
    data: UserProfileUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    try:
        user = await update_user_profile(
            db=db,
            user_id=current_user.id,
            phone=data.phone,
            old_password=data.old_password,
            new_password=data.new_password,
            confirm_password=data.confirm_password,
            full_name=data.full_name,
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

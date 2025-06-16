from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import async_session
from app.utils.selectors.barber import get_barber_id_by_user_id
from app.utils.selectors.user import get_user_with_barber_profile_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)


async def get_session():
    async with async_session() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("id")
    if user_id is None:
        raise credentials_exception

    user = await get_user_with_barber_profile_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception

    return user


async def get_current_user_info(
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("id")
    role = payload.get("role")
    if user_id is None or role is None:
        raise credentials_exception

    return {"id": user_id, "role": role}


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme_optional),
) -> dict | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except Exception:
        return None
    if not payload:
        return None
    user_id = payload.get("id")
    role = payload.get("role")
    if user_id is None or role is None:
        return None
    return {"id": user_id, "role": role}


async def get_current_barber_id(
    db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user_info)
) -> int:
    return await get_barber_id_by_user_id(db, current_user["id"])

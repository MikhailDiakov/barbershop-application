from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.db.session import async_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)


async def get_session():
    async with async_session() as session:
        yield session


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

    return {"id": int(user_id), "role": role}


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
    return {"id": int(user_id), "role": role}

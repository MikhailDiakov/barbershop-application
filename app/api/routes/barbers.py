from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.security import get_current_user_info
from app.services.barber_service import remove_barber_photo, upload_barber_photo

router = APIRouter()


@router.post("/avatar")
async def upload_own_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    barber = await upload_barber_photo(
        db=db, barber_id=current_user["id"], file=file, user_role=current_user["role"]
    )
    return {"avatar_url": barber.avatar_url}


@router.delete("/avatar")
async def delete_own_avatar(
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await remove_barber_photo(
        db=db,
        barber_id=current_user["id"],
        user_role=current_user["role"],
    )
    return {"detail": "Avatar deleted"}

import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    barber_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str]


class ReviewRead(BaseModel):
    id: int
    client_id: int
    barber_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime.datetime: lambda v: v.strftime("%Y-%m-%d %H:%M"),
        }


class ReviewAdminRead(ReviewRead):
    is_approved: bool


class ReviewReadForBarber(BaseModel):
    id: int
    client_name: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime.datetime: lambda v: v.strftime("%Y-%m-%d %H:%M"),
        }

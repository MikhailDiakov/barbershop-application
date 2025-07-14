import re
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.schemas.review import ReviewReadForBarber
from app.schemas.validators import (
    validate_password_complexity,
    validate_phone,
    validate_username_length,
)


class BarberBase(BaseModel):
    full_name: str | None = None


class BarberCreate(BarberBase):
    username: str
    phone: str
    password: str

    @field_validator("username")
    def username_length(cls, v: str) -> str:
        return validate_username_length(v)

    @field_validator("phone")
    def phone_valid(cls, v: str) -> str:
        return validate_phone(v)

    @field_validator("password")
    def password_valid(cls, v: str) -> str:
        return validate_password_complexity(v)


class BarberOut(BarberBase):
    id: int
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class BarberOutwithReviews(BarberBase):
    id: int
    avatar_url: Optional[str] = None
    avg_rating: float = 0.0
    reviews_count: int = 0

    class Config:
        from_attributes = True


class BarberUpdate(BaseModel):
    full_name: Optional[str] = None

    @field_validator("full_name")
    def name_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Full name must be at least 3 characters long")
        if not re.fullmatch(r"[^\W\d_]+(?: [^\W\d_]+)*", v, re.UNICODE):
            raise ValueError("Full name must contain only letters and spaces")
        return v


class BarberOutwithReviewsDetailed(BaseModel):
    id: int
    full_name: str
    avatar_url: Optional[str] = None
    avg_rating: float
    reviews_count: int
    reviews: List[ReviewReadForBarber]

    class Config:
        from_attributes = True
        from_attributes = True

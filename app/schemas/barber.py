from typing import Optional

from pydantic import BaseModel, field_validator

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


class BarberUpdate(BaseModel):
    full_name: Optional[str] = None


class BarberInfo(BaseModel):
    full_name: Optional[str]
    avatar_url: Optional[str]

    class Config:
        from_attributes = True


class BarberProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

from app.schemas.validators import (
    validate_password_complexity,
    validate_phone,
    validate_username_length,
)


class UserCreate(BaseModel):
    username: str
    phone: str
    password: str
    confirm_password: str

    @field_validator("username")
    def username_length(cls, v: str) -> str:
        return validate_username_length(v)

    @field_validator("phone")
    def phone_valid(cls, v):
        return validate_phone(v)

    @field_validator("password")
    def password_complexity(cls, v):
        return validate_password_complexity(v)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserRead(BaseModel):
    id: int
    username: str
    phone: str
    role_id: Optional[int]

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    phone: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None
    confirm_password: Optional[str] = None

    @field_validator("phone")
    def phone_valid(cls, v):
        if v is None:
            return v
        return validate_phone(v)

    @field_validator("new_password")
    def password_complexity(cls, v):
        if v is None:
            return v
        return validate_password_complexity(v)

    @model_validator(mode="after")
    def passwords_match(cls, values):
        if values.new_password or values.confirm_password:
            if values.new_password != values.confirm_password:
                raise ValueError("Passwords do not match")
            if not values.old_password:
                raise ValueError("Old password is required to change password")
        return values


class PasswordResetRequest(BaseModel):
    phone: str


class PasswordResetConfirm(BaseModel):
    phone: str
    code: str
    new_password: str
    new_password_repeat: str

    @field_validator("new_password")
    def password_complexity(cls, v):
        return validate_password_complexity(v)

    @model_validator(mode="after")
    def passwords_match(cls, values):
        if values.new_password != values.new_password_repeat:
            raise ValueError("Passwords do not match")
        return values


class UserUpdateForAdmin(BaseModel):
    username: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

    @field_validator("username")
    def username_length(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_username_length(v)

    @field_validator("phone")
    def phone_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_phone(v)

    @field_validator("password")
    def password_complexity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_password_complexity(v)


class PromoteUserToBarberRequest(BaseModel):
    full_name: str


class AdminOut(BaseModel):
    id: int
    username: str
    phone: str
    role_id: int

    class Config:
        from_attributes = True

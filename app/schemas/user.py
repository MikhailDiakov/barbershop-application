import re
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


def validate_phone(phone: str) -> str:
    if not re.fullmatch(r"\+?\d{10,15}", phone):
        raise ValueError("Phone must be 10-15 digits, can start with +")
    return phone


def validate_password_complexity(password: str) -> str:
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[A-Za-zА-Яа-я]", password):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"[\W_]", password):
        raise ValueError("Password must contain at least one special character")
    return password


class UserCreate(BaseModel):
    username: str
    phone: str
    password: str
    confirm_password: str

    @field_validator("username")
    def username_length(cls, v):
        if not (3 <= len(v) <= 50):
            raise ValueError("Username must be between 3 and 50 characters")
        return v

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
        orm_mode = True


class UserPhoneUpdate(BaseModel):
    phone: str
    password: str

    @field_validator("phone")
    def phone_valid(cls, v):
        if v is None:
            return v
        return validate_phone(v)


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    def password_complexity(cls, v):
        return validate_password_complexity(v)

    @model_validator(mode="after")
    def passwords_match(cls, values):
        if values.new_password != values.confirm_password:
            raise ValueError("Passwords do not match")
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

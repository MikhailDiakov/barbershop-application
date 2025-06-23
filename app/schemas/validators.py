import re

from app.utils.logger import logger


def validate_phone(phone: str) -> str:
    if not re.fullmatch(r"\+?\d{10,15}", phone):
        logger.warning(
            "Phone validation failed", extra={"field": "phone", "value": phone}
        )
        raise ValueError("Phone must be 10-15 digits, can start with +")
    return phone


def validate_password_complexity(password: str) -> str:
    if len(password) < 6:
        logger.warning(
            "Password too short", extra={"field": "password", "value": password}
        )
        raise ValueError("Password must be at least 6 characters long")
    if not re.search(r"\d", password):
        logger.warning(
            "Password lacks digit", extra={"field": "password", "value": password}
        )
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[A-Za-zА-Яа-я]", password):
        logger.warning(
            "Password lacks letter", extra={"field": "password", "value": password}
        )
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"[\W_]", password):
        logger.warning(
            "Password lacks special character",
            extra={"field": "password", "value": password},
        )
        raise ValueError("Password must contain at least one special character")
    return password


def validate_username_length(username: str) -> str:
    if not (3 <= len(username) <= 50):
        logger.warning(
            "Username length invalid", extra={"field": "username", "value": username}
        )
        raise ValueError("Username must be between 3 and 50 characters")
    return username

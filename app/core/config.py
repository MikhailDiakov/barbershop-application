import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Barbershop"
    DB_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./barbershop.db")
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret")
    ALGORITHM = "HS256"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER")


settings = Settings()

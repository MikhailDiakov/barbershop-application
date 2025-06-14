import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Barbershop"

    # DB
    DB_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./barbershop.db")

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret")
    ALGORITHM = "HS256"

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # SuperAdmin
    SUPERADMIN_LOGIN: str = os.getenv("SUPERADMIN_LOGIN", "admin123")
    SUPERADMIN_PASSWORD: str = os.getenv("SUPERADMIN_PASSWORD", "admin123")

    # Twilio
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER")

    # AWS S3
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME")


settings = Settings()

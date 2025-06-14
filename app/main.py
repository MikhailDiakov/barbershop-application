import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from app.api.routes import barbers, users
from app.api.routes.admin import admin_router
from app.api.routes.admin.superadmin import router as superadmin_router
from app.core.config import settings

app = FastAPI()


@app.on_event("startup")
async def startup():
    redis_connection = redis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(barbers.router, prefix="/barbers", tags=["barbers"])
app.include_router(superadmin_router, prefix="/superadmin", tags=["superadmin"])

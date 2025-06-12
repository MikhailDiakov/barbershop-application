import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from app.api.routes import users

app = FastAPI()


@app.on_event("startup")
async def startup():
    redis_connection = redis.from_url(
        "redis://localhost", encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)


app.include_router(users.router, prefix="/users", tags=["users"])

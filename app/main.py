import redis.asyncio as redis
import sentry_sdk
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from starlette_exporter import PrometheusMiddleware, handle_metrics

from app.api.routes import ai_assistant, appointments, barbers, review, users
from app.api.routes.admin import admin_router
from app.api.routes.admin.superadmin import router as superadmin_router
from app.core.config import settings
from app.utils.logger import es_client, logger

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[
        FastApiIntegration(),
        LoggingIntegration(level=None, event_level="ERROR"),
    ],
    traces_sample_rate=1.0,
    send_default_pii=True,
)


app = FastAPI()

app.add_middleware(PrometheusMiddleware)

app.add_route("/metrics", handle_metrics)


@app.on_event("startup")
async def startup():
    redis_connection = redis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)
    logger.info("Application startup: FastAPILimiter initialized, Redis connected")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Application shutdown: closing Elasticsearch client")
    await es_client.close()


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(barbers.router, prefix="/barber", tags=["barbers"])
app.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
app.include_router(review.router, prefix="/review", tags=["review"])
app.include_router(ai_assistant.router, prefix="/ai-assistant", tags=["AI Assistant"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(superadmin_router, prefix="/superadmin", tags=["superadmin"])

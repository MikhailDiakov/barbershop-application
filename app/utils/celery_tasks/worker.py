from celery import Celery

from app.core.config import settings
from app.utils.celery_tasks.sms import send_sms

celery = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


@celery.task
def send_sms_task(to_phone: str, message: str):
    return send_sms(to_phone, message)

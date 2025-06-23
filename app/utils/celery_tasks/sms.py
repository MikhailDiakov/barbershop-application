# from celery import Celery
# from twilio.rest import Client

# from app.core.config import settings
# from app.utils.logger import logger

# celery = Celery(
#     "worker",
#     broker=settings.REDIS_URL,
#     backend=settings.REDIS_URL,
# )

# twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


# @celery.task
# def send_sms_task(to_phone: str, message: str):
#     logger.info(f"Sending SMS to {to_phone} with message: {message}")
#     try:
#         msg = twilio_client.messages.create(
#             body=message,
#             from_=settings.TWILIO_PHONE_NUMBER,
#             to=to_phone,
#         )
#         logger.info(f"SMS sent successfully to {to_phone}, sid: {msg.sid}")
#         return msg.sid
#     except Exception as e:
#         logger.error(f"Failed to send SMS to {to_phone}: {e}")
#         raise

from celery import Celery

from app.core.config import settings
from app.utils.logger import logger

celery = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


@celery.task
def send_sms_task(to_phone: str, message: str):
    logger.info(f"Sending SMS to {to_phone} with message: {message}")
    print(f"[MOCK SMS] To: {to_phone}, Message: {message}")
    logger.info(f"SMS sent successfully to {to_phone}")
    return "mocked-message-id"

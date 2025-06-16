# from celery import Celery
# from twilio.rest import Client

# from app.core.config import settings

# celery = Celery(
#     "worker",
#     broker=settings.REDIS_URL,
#     backend=settings.REDIS_URL,
# )

# twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


# @celery.task
# def send_sms_task(to_phone: str, message: str):
#     message = twilio_client.messages.create(
#         body=message,
#         from_=settings.TWILIO_PHONE_NUMBER,
#         to=to_phone,
#     )
#     return message.sid

from celery import Celery

from app.core.config import settings

celery = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


@celery.task
def send_sms_task(to_phone: str, message: str):
    print(f"[MOCK SMS] To: {to_phone}, Message: {message}")
    return "mocked-message-id"

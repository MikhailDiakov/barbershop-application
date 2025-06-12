from twilio.rest import Client

from app.core.config import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_sms(to_phone: str, message: str):
    message = client.messages.create(
        body=message, from_=settings.TWILIO_PHONE_NUMBER, to=to_phone
    )
    return message.sid

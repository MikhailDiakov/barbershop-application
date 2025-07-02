from openai import OpenAI

from app.core.config import settings
from app.utils.redis_client import load_barbershop_info

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def ask_barber_ai(user_question: str) -> str:
    shop_info = await load_barbershop_info()
    services = ", ".join(shop_info.get("services", []))

    system_prompt = f"""
You are a friendly, professional virtual barber working at a premium barbershop.

You answer user questions about the shop using the info below. Be helpful, casual but respectful, and give suggestions when appropriate.

Barbershop Description:
{shop_info.get("description")}

Address: {shop_info.get("address")}
Working Hours: {shop_info.get("working_hours")}
Services: {services}

Extra Notes:
{shop_info.get("notes")}

Do not give personal info about barbers or bookings — instead, mention that users can check barbers and book appointments via the appropriate sections or endpoints.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ],
        temperature=0.7,
        max_tokens=500,
        # store=True,
    )

    return response.choices[0].message.content

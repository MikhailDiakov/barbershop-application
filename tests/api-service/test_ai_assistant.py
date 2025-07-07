from unittest.mock import patch

import pytest


def fake_create(*args, **kwargs):
    class FakeChoice:
        message = type("Message", (), {"content": "Mocked response"})()

    class FakeResponse:
        choices = [FakeChoice()]

    return FakeResponse()


async def fake_load_barbershop_info():
    return {
        "description": "Best barbershop in town",
        "address": "123 Main St",
        "working_hours": "9am - 6pm",
        "services": ["Haircut", "Shave"],
        "notes": "No personal info shared",
    }


@pytest.mark.asyncio
@patch(
    "app.services.ai_assistant_service.client.chat.completions.create",
    side_effect=fake_create,
)
@patch(
    "app.services.ai_assistant_service.load_barbershop_info",
    side_effect=fake_load_barbershop_info,
)
async def test_ask_ai_success(mock_load_info, mock_create, client):
    response = await client.post("/ai-assistant/ask", json={"question": "How are you?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "Mocked response"}
    mock_load_info.assert_awaited_once()
    mock_create.assert_called_once()

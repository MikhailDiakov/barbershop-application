from unittest.mock import patch

import pytest


def fake_create(*args, **kwargs):
    class FakeChoice:
        message = type("Message", (), {"content": "Mocked response"})

    class FakeResponse:
        choices = [FakeChoice()]

    return FakeResponse()


@pytest.mark.asyncio
@patch(
    "app.services.ai_assistant_service.client.chat.completions.create",
    side_effect=fake_create,
)
async def test_ask_ai_success(mock_create, client):
    response = await client.post("/ai-assistant/ask", json={"question": "How are you?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "Mocked response"}

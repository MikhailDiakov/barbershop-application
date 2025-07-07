from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.utils.celery_tasks.sms import send_sms_task


@pytest.mark.asyncio
@patch("app.utils.celery_tasks.sms.twilio_client.messages.create")
def test_send_sms_task_success(mock_create):
    mock_msg = MagicMock()
    mock_msg.sid = "fake_sid_123"
    mock_create.return_value = mock_msg

    sid = send_sms_task("1234567890", "Test message")

    mock_create.assert_called_once_with(
        body="Test message",
        from_=settings.TWILIO_PHONE_NUMBER,
        to="1234567890",
    )
    assert sid == "fake_sid_123"


@pytest.mark.asyncio
@patch("app.utils.celery_tasks.sms.twilio_client.messages.create")
def test_send_sms_task_failure(mock_create):
    mock_create.side_effect = Exception("Twilio error")

    with pytest.raises(Exception):
        send_sms_task("1234567890", "Test message")

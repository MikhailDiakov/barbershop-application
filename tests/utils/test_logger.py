import asyncio
from logging import LogRecord
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.utils.logger import ElasticsearchHandler


@pytest.mark.asyncio
async def test_send_logs_to_elasticsearch():
    mock_es_client = MagicMock()
    mock_es_client.index = AsyncMock(return_value={"result": "created"})

    handler = ElasticsearchHandler(mock_es_client, "test-index")

    record = LogRecord(
        name="test_logger",
        level=20,  # INFO
        pathname="test_file.py",
        lineno=42,
        msg="Test log message",
        args=(),
        exc_info=None,
    )

    record.funcName = "test_func"

    await handler._send(record)

    mock_es_client.index.assert_awaited_once()
    args, kwargs = mock_es_client.index.call_args
    assert kwargs["index"] == "test-index"
    doc = kwargs["document"]
    assert doc["level"] == "INFO"
    assert doc["message"] == "Test log message"
    assert doc["logger_name"] == "test_logger"


def test_emit_creates_task(monkeypatch):
    mock_es_client = MagicMock()
    mock_es_client.index = AsyncMock()

    handler = ElasticsearchHandler(mock_es_client, "test-index")

    record = MagicMock()
    record.levelname = "INFO"
    record.getMessage.return_value = "Test message"
    record.name = "test_logger"
    record.filename = "test_file.py"
    record.funcName = "test_func"
    record.lineno = 123
    record.__dict__ = {}

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    called = {}

    def fake_create_task(coro):
        called["called"] = True
        return asyncio.ensure_future(coro)

    monkeypatch.setattr(loop, "create_task", fake_create_task)

    handler.emit(record)

    assert called.get("called") is True

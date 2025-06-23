import asyncio
import datetime
import logging
from logging import LogRecord

from elasticsearch import AsyncElasticsearch

from app.core.config import settings

ELASTICSEARCH_HOST = settings.ELASTICSEARCH_URL
ES_INDEX = "app-logs"


class ElasticsearchHandler(logging.Handler):
    def __init__(self, es_client: AsyncElasticsearch, index: str):
        super().__init__()
        self.es_client = es_client
        self.index = index

    def emit(self, record: LogRecord):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            try:
                loop.create_task(self._send(record))
            except Exception as e:
                print("Elasticsearch logging failed (emit):", str(e))
        else:
            try:
                loop.run_until_complete(self._send(record))
            except Exception as e:
                print("Elasticsearch logging failed (run):", str(e))

    async def _send(self, record: LogRecord):
        log_doc = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger_name": record.name,
            "filename": record.filename,
            "funcName": record.funcName,
            "lineno": record.lineno,
            **{
                k: v
                for k, v in record.__dict__.items()
                if k
                not in (
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                )
            },
        }

        try:
            await self.es_client.index(index=self.index, document=log_doc)
        except Exception as e:
            print(f"[Logger] Failed to send log to Elasticsearch: {e}")


es_client = AsyncElasticsearch(hosts=[ELASTICSEARCH_HOST])
es_handler = ElasticsearchHandler(es_client, ES_INDEX)

logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)
logger.addHandler(es_handler)
logger.propagate = False

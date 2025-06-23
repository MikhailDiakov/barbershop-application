FROM python:3.12-slim

RUN apt-get update && apt-get upgrade -y && apt-get clean

ENV PYTHONUNBUFFERED=1
WORKDIR /app/

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

ENV PATH="/app/.venv/bin:$PATH"

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock /app/

RUN uv sync --frozen --no-install-project

COPY ./app /app/app
COPY ./scripts /app/scripts
COPY ./alembic.ini /app/
COPY ./alembic /app/alembic

RUN uv sync

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

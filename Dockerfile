# syntax=docker/dockerfile:1.7

FROM python:3.14-slim-bookworm AS base

COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /uvx /bin/

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

FROM base AS development

RUN uv sync --frozen --all-groups

CMD ["arendabot-polling"]

FROM base AS builder

RUN uv sync --frozen --no-dev --no-editable

FROM python:3.14-slim-bookworm AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system arendabot \
    && useradd --system --gid arendabot --home-dir /app arendabot

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY alembic.ini ./
COPY src ./src

USER arendabot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]

CMD ["uvicorn", "arendabot.adapters.web.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

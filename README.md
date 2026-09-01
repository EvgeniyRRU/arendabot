# arendabot

A Python 3.14 foundation for an asynchronous Telegram bot. It uses aiogram for Telegram,
FastAPI for production webhooks, async SQLAlchemy and Alembic for PostgreSQL, and uv for a
locked development and deployment toolchain.

The repository intentionally contains no user-facing bot commands. Its seed domain model and
application service demonstrate the ports-and-adapters boundaries without imposing product
behavior.

## Architecture

- `domain` contains the framework-independent `TelegramUser` entity.
- `application` contains repository/unit-of-work ports and `SyncTelegramUser`.
- `adapters` contains PostgreSQL, Telegram, and ASGI implementations.
- `bootstrap` owns settings, logging, dependency composition, and executable entry points.

Development uses long polling, so it does not need a public HTTPS endpoint. Production runs an
ASGI webhook and validates Telegram's `X-Telegram-Bot-Api-Secret-Token` header.

## Requirements

- uv
- Docker with Docker Compose
- A bot token created through [BotFather](https://t.me/BotFather)

Python 3.14 does not need to be installed separately; uv installs the version declared in
`.python-version`.

## Local setup

Copy the example environment and replace the bot token:

```bash
cp .env.example .env
uv python install 3.14
uv sync --locked --all-groups
```

Run the complete development environment with source reload:

```bash
docker compose up --build
```

Compose starts PostgreSQL 18, waits for it to become healthy, applies migrations, removes any
registered webhook, and starts polling. Stop it with `docker compose down`. The database is kept
in the `postgres-data` volume; use `docker compose down --volumes` only when you intentionally
want to delete local database data.

To run Python locally while PostgreSQL stays in Docker, start only the database, change the
database host in `.env` from `postgres` to `localhost`, then run migrations and polling:

```bash
docker compose up -d postgres
uv run alembic upgrade head
uv run arendabot-polling
```

## Database migrations

Create and inspect a migration after changing SQLAlchemy metadata:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic downgrade -1
```

Production migrations are an explicit deployment step. Run them once before replacing app
containers rather than from every replica.

## Quality checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Integration tests use Testcontainers to start PostgreSQL 18 and therefore require a working local
Docker daemon. They apply the real Alembic migration and do not call Telegram.

## Production image

Build the non-root production target:

```bash
docker build --target production -t arendabot:latest .
```

Set these environment variables when running it:

- `ARENDABOT_BOT_TOKEN`
- `ARENDABOT_DATABASE_URL` using the `postgresql+asyncpg://` driver
- `ARENDABOT_UPDATE_MODE=webhook`
- `ARENDABOT_WEBHOOK_BASE_URL`, the externally reachable HTTPS base URL
- `ARENDABOT_WEBHOOK_SECRET`, 1–256 letters, digits, underscores, or hyphens

Apply migrations with the same image and production environment:

```bash
docker run --rm --env-file .env arendabot:latest alembic upgrade head
```

Then run the ASGI service:

```bash
docker run --rm --env-file .env -p 8000:8000 arendabot:latest
```

The service registers `<ARENDABOT_WEBHOOK_BASE_URL>/telegram/webhook` at startup. It exposes
`/health/live` for process liveness and `/health/ready` for PostgreSQL readiness. TLS termination
and the production PostgreSQL service are expected to be provided by the deployment platform.

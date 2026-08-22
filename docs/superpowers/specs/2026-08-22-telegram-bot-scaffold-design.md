# Telegram Bot Scaffold Design

## Goal

Create `arendabot`, a Python 3.14 Telegram bot foundation with a clean ports-and-adapters architecture, reproducible tooling, PostgreSQL persistence, local containers, production packaging, and automated checks.

## Architecture

The `src/arendabot` package separates framework-independent domain and application code from Telegram, PostgreSQL, and ASGI adapters. A composition root owns settings and lifecycle wiring. Development consumes updates through aiogram polling; production receives secret-validated Telegram webhooks through FastAPI.

The seed domain consists of a `TelegramUser` entity, repository and unit-of-work ports, and a profile synchronization use case. SQLAlchemy models and mappings stay in the PostgreSQL adapter. The use case is tested but is not exposed through a bot command.

## Runtime and Operations

The ASGI application exposes process liveness, database readiness, and the Telegram webhook. Production registers its webhook idempotently at startup and retains it at shutdown. Development polling removes the webhook before consuming updates. Configuration fails fast when mode-specific settings are missing.

Alembic migrations are explicit in production and run before the single development app starts. The production image is lockfile-driven and non-root. Docker Compose runs the app and PostgreSQL 18 with source reload. GitHub Actions runs linting, formatting, type checks, tests with PostgreSQL Testcontainers, Compose validation, and an image build.

## Testing

Domain and application behavior use fakes. ASGI tests replace Telegram and database boundaries and never call Telegram. PostgreSQL integration tests apply Alembic and exercise constraints, repository persistence, rollback, and readiness against a Testcontainer.


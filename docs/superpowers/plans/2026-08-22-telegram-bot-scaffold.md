# Telegram Bot Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a production-ready Python 3.14 Telegram bot foundation.

**Architecture:** Use ports and adapters around a pure Telegram user domain. Compose aiogram, FastAPI, and async SQLAlchemy at runtime while keeping framework types outside domain and application code.

**Tech Stack:** Python 3.14, uv, aiogram, FastAPI/ASGI, SQLAlchemy, asyncpg, Alembic, PostgreSQL 18, pytest, Testcontainers, Ruff, Pyright, Docker Compose, Docker, GitHub Actions.

---

### Task 1: Project and Tooling

- [ ] Create the uv package metadata, Python pin, dependency lock, and Ruff/Pyright/pytest configuration.
- [ ] Add the `src` package, test layout, and environment example.
- [ ] Verify locked installation and empty-suite tool execution.

### Task 2: Domain and Application

- [ ] Write failing tests for Telegram user creation and synchronization.
- [ ] Implement the pure entity, repository/unit-of-work protocols, command, and use case.
- [ ] Run tests and static checks, then commit.

### Task 3: PostgreSQL Adapter

- [ ] Write failing Testcontainer tests for migration, persistence, uniqueness, and rollback.
- [ ] Implement the async engine/session factory, SQLAlchemy mapping, repository, unit of work, and initial Alembic migration.
- [ ] Run unit/integration tests and static checks, then commit.

### Task 4: Telegram and ASGI Adapters

- [ ] Write failing tests for settings, health endpoints, webhook authentication/validation/dispatch, lifecycle, and polling startup.
- [ ] Implement typed settings, application composition, FastAPI lifespan/routes, webhook registration, empty router, and polling entry point.
- [ ] Run runtime tests and static checks, then commit.

### Task 5: Containers, CI, and Documentation

- [ ] Add the development Compose stack and non-root multi-stage production Dockerfile.
- [ ] Add GitHub Actions and document all local, migration, testing, and deployment workflows.
- [ ] Verify Ruff, formatting, Pyright, pytest, Compose configuration, and the production image build.


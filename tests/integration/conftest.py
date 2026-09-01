from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import URL, make_url
from testcontainers.community.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[URL]:
    with PostgresContainer("postgres:18-alpine") as postgres:
        url = make_url(postgres.get_connection_url()).set(drivername="postgresql+asyncpg")
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False))
        command.upgrade(config, "head")
        yield url

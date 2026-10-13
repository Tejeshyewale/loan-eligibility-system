"""Alembic environment: URL always comes from app settings (.env / Render),
never from alembic.ini (its sqlalchemy.url is a violently-ignored placeholder).
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy import create_engine

from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from src.core.settings import DATABASE_URL  # noqa: E402
from src.database.db import resolve_database_url  # noqa: E402
from src.database.models import Base  # noqa: E402

target_metadata = Base.metadata
DB_URL = resolve_database_url(DATABASE_URL)


def run_migrations_offline() -> None:
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    kwargs = {"poolclass": pool.NullPool}
    if DB_URL.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    connectable = create_engine(DB_URL, **kwargs)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

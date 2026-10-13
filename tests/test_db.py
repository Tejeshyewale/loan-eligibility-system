"""DB-layer tests: URL normalization (Render-style schemes) and engine setup.

The driver is psycopg v3 (never psycopg2): every Postgres URL must come out
as postgresql+psycopg://, which is what alembic/env.py and the app engine
both consume via resolve_database_url().
"""
from src.database.db import resolve_database_url


def test_postgres_scheme_normalized():
    assert resolve_database_url("postgres://u:p@host:5432/db") == \
        "postgresql+psycopg://u:p@host:5432/db"


def test_bare_postgresql_scheme_gets_psycopg_driver():
    assert resolve_database_url("postgresql://u:p@host/db") == \
        "postgresql+psycopg://u:p@host/db"


def test_explicit_psycopg_scheme_passes_through():
    url = "postgresql+psycopg://u:p@host:5432/db"
    assert resolve_database_url(url) == url


def test_sqlite_passes_through():
    assert resolve_database_url("sqlite:///./loan.db") == "sqlite:///./loan.db"


def test_sqlite_engine_has_thread_guard():
    from sqlalchemy import create_engine

    url = resolve_database_url("sqlite:///./loan.db")
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    eng = create_engine(url, **kwargs)
    assert eng.url.get_backend_name() == "sqlite"


def test_postgres_url_selects_psycopg_dialect():
    """The normalized URL must bind the psycopg (v3) DBAPI, not psycopg2."""
    from sqlalchemy import create_engine

    eng = create_engine(resolve_database_url("postgres://u:p@host:5432/db"))
    assert eng.url.get_backend_name() == "postgresql"
    assert eng.driver == "psycopg"

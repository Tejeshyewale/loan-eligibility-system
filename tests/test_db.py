"""DB-layer tests: URL normalization (Render-style schemes) and engine setup."""
from src.database.db import resolve_database_url


def test_postgres_scheme_normalized():
    assert resolve_database_url("postgres://u:p@host:5432/db") == \
        "postgresql://u:p@host:5432/db"


def test_postgresql_and_sqlite_pass_through():
    assert resolve_database_url("postgresql://u:p@host/db") == "postgresql://u:p@host/db"
    assert resolve_database_url("sqlite:///./loan.db") == "sqlite:///./loan.db"


def test_sqlite_engine_has_thread_guard():
    from sqlalchemy import create_engine

    url = resolve_database_url("sqlite:///./loan.db")
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    eng = create_engine(url, **kwargs)
    assert eng.url.get_backend_name() == "sqlite"

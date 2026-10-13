"""Engine + sessions for sqlite (local/dev/tests) and Postgres (Render).

- Accepts Render's `postgres://` scheme by normalizing to `postgresql://`.
- `pool_pre_ping` guards against stale pooled connections (matters for
  Postgres; harmless for sqlite).
- sqlite keeps `check_same_thread=False` for the local single-process dev
  server; never pass it to Postgres.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.settings import DATABASE_URL


def resolve_database_url(url: str = DATABASE_URL) -> str:
    """Normalize a database URL for SQLAlchemy + the psycopg v3 driver.

    - Render/Heroku-style ``postgres://...`` -> ``postgresql+psycopg://...``.
    - Bare ``postgresql://...`` (SQLAlchemy's default dialect, which wants
      psycopg2) -> ``postgresql+psycopg://...`` so we always use psycopg v3.
    - ``postgresql+psycopg://...`` and ``sqlite://...`` pass through.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


RESOLVED_DATABASE_URL = resolve_database_url()

_engine_kwargs: dict = {"pool_pre_ping": True}
if RESOLVED_DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(RESOLVED_DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

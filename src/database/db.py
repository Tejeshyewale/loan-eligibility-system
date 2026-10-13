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
    """Normalize a database URL for SQLAlchemy.

    Render/Heroku-style `postgres://...` is not a SQLAlchemy scheme;
    rewrite it to `postgresql://...`. Everything else passes through.
    """
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
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

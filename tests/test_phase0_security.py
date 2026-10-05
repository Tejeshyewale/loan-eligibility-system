"""Phase 0 security tests: role escalation, secret fail-fast, rate limit, rehash."""
import hashlib
import logging
import os
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _child_env(**overrides):
    env = dict(os.environ)
    env.pop("JWT_SECRET_KEY", None)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env.update(overrides)
    return env


def test_signup_role_admin_still_creates_user(client, db_session):
    """A 'role': 'admin' smuggled in the signup body must be ignored."""
    from src.database.models import User

    res = client.post("/auth/signup", json={
        "username": "sneaky_admin", "password": "secret123", "role": "admin",
    })
    assert res.status_code == 200
    db_session.expire_all()
    user = db_session.query(User).filter(User.username == "sneaky_admin").one()
    assert user.role == "user"


def test_app_fails_without_secret_key(tmp_path):
    """Importing settings with no secret and no .env must fail fast."""
    proc = subprocess.run(
        [sys.executable, "-c", "import src.core.settings"],
        cwd=tmp_path,  # no .env here
        env=_child_env(),
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode != 0
    assert "JWT_SECRET_KEY" in (proc.stderr + proc.stdout)


def test_legacy_sha256_login_rehashes_to_bcrypt(client, db_session):
    """Correct legacy-hash login succeeds AND upgrades the stored hash."""
    import bcrypt
    from src.database.models import User

    legacy_hex = hashlib.sha256(b"oldpass123").hexdigest()
    db_session.add(User(username="legacy_user", password=legacy_hex, role="user"))
    db_session.commit()

    res = client.post("/auth/login", json={"username": "legacy_user", "password": "oldpass123"})
    assert res.status_code == 200
    assert "access_token" in res.json()

    db_session.expire_all()
    stored = db_session.query(User).filter(User.username == "legacy_user").one().password
    assert stored != legacy_hex
    assert stored.startswith("$2b$")
    assert bcrypt.checkpw(b"oldpass123", stored.encode())


def test_startup_creates_tables_on_empty_db(tmp_path, monkeypatch):
    """Lifespan must create all tables when pointed at a fresh empty DB file."""
    import asyncio
    from sqlalchemy import create_engine, inspect

    import src.api.main as main_module
    from src.database.models import Base as models_base

    fresh = tmp_path / "fresh.db"
    assert not fresh.exists()
    scratch = create_engine(f"sqlite:///{fresh}")
    monkeypatch.setattr(main_module, "engine", scratch)

    async def _run():
        async with main_module.lifespan(main_module.app):
            pass

    asyncio.run(_run())
    tables = set(inspect(scratch).get_table_names())
    expected = set(models_base.metadata.tables.keys())
    assert expected, "models define no tables"
    assert expected <= tables


def test_logging_never_leaks_secrets(client, auth_headers, caplog):
    """Middleware/logs must not contain bodies, passwords, or tokens."""
    import re

    with caplog.at_level(logging.INFO):
        client.post("/auth/login",
                    json={"username": "leak_probe_user_xyz", "password": "SuperSecretPW123"})
        client.get("/", headers=auth_headers)
    text = caplog.text
    assert "SuperSecretPW123" not in text
    assert "Bearer" not in text
    assert "authorization" not in text.lower()
    assert re.search(r"password", text, re.IGNORECASE) is None


def test_login_rate_limit_triggers(tmp_path):
    """With a 2/minute login limit, the 3rd rapid login must 429."""
    probe = tmp_path / "rate_probe.py"
    probe.write_text(textwrap.dedent("""\
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from src.api.main import app
        from src.database.db import get_db
        from src.database.models import Base

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        TestingSession = sessionmaker(bind=engine)

        def _override():
            session = TestingSession()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = _override
        with TestClient(app) as client:
            client.post("/auth/signup", json={"username": "rl_user", "password": "secret123"})
            codes = []
            for _ in range(3):
                r = client.post("/auth/login", json={"username": "rl_user", "password": "secret123"})
                codes.append(r.status_code)
            print("CODES:", codes)
            assert codes[0] == 200 and codes[1] == 200 and codes[2] == 429, codes
    """))
    proc = subprocess.run(
        [sys.executable, str(probe)],
        cwd=tmp_path,  # no .env here; env below supplies the secret
        env=_child_env(
            JWT_SECRET_KEY="test-only-secret-not-for-production",
            RATE_LIMIT_LOGIN="2/minute",
            RATE_LIMIT_PREDICT="1000/minute",
            RATE_LIMIT_EXPLAIN="1000/minute",
        ),
        capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, "STDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr[-2000:]

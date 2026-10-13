"""Phase 0 security tests: role escalation, secret fail-fast, rate limit, rehash."""
import hashlib
import logging
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

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


def test_default_login_limit_is_5_per_minute():
    """Production default for /login must stay 5/minute (no inspection of env)."""
    from src.core.settings import Settings

    assert Settings.model_fields["RATE_LIMIT_LOGIN"].default == "5/minute"


def test_default_trusted_proxy_hops_is_1():
    """One trusted proxy hop (Render) unless the deploy overrides it."""
    from src.core.settings import Settings

    assert Settings.model_fields["TRUSTED_PROXY_HOPS"].default == 1


def _xff_request(xff=None, host="5.6.7.8"):
    from starlette.requests import Request

    headers = []
    if xff is not None:
        headers.append((b"x-forwarded-for", xff.encode()))
    return Request({"type": "http", "headers": headers, "client": (host, 5000)})


def test_get_client_ip_trusts_rightmost():
    from src.api.rate_limit import get_client_ip

    assert get_client_ip(_xff_request("9.9.9.9, 10.0.0.1")) == "10.0.0.1"


def test_get_client_ip_falls_back_to_peer(monkeypatch):
    import src.api.rate_limit as rl
    from src.core import settings as settings_module

    assert rl.get_client_ip(_xff_request()) == "5.6.7.8"  # no header
    monkeypatch.setattr(settings_module.settings, "TRUSTED_PROXY_HOPS", 2)
    assert rl.get_client_ip(_xff_request("9.9.9.9")) == "5.6.7.8"  # chain too short


def test_login_rate_limit_triggers(tmp_path):
    """With a 2/minute login limit: (a) a client replaying a spoofed
    leftmost XFF entry on every request still shares ONE budget keyed on
    the trusted rightmost IP and gets 429 on the 3rd attempt; (b) a
    genuinely different rightmost IP gets a fresh budget."""
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
            body = {"username": "rl_user", "password": "secret123"}
            # (a) spoofed leftmost entry, stable trusted rightmost entry.
            codes_a = []
            for _ in range(3):
                r = client.post("/auth/login", json=body,
                                headers={"X-Forwarded-For": "9.9.9.9, 10.0.0.1"})
                codes_a.append(r.status_code)
            print("CODES_A:", codes_a)
            assert codes_a == [200, 200, 429], codes_a
            # (b) different trusted rightmost IP -> separate budget.
            r = client.post("/auth/login", json=body,
                            headers={"X-Forwarded-For": "9.9.9.9, 10.0.0.2"})
            print("CODES_B:", r.status_code)
            assert r.status_code == 200, r.status_code
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


def test_negative_proxy_hops_rejected():
    """TRUSTED_PROXY_HOPS=-1 must fail settings validation, not silently run."""
    from pydantic import ValidationError

    from src.core.settings import Settings

    with pytest.raises(ValidationError):
        Settings(TRUSTED_PROXY_HOPS=-1)


def test_hops_zero_ignores_xff_entirely(tmp_path):
    """Direct-serve mode (hops=0): 6 logins with a *different* spoofed XFF
    each time still share the peer budget -> 5x200 then 429."""
    probe = tmp_path / "rate_probe_zero.py"
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
            client.post("/auth/signup", json={"username": "rl0_user", "password": "secret123"})
            body = {"username": "rl0_user", "password": "secret123"}
            codes = []
            for i in range(6):
                r = client.post("/auth/login", json=body,
                                headers={"X-Forwarded-For": f"9.9.9.{i}, 10.0.0.1"})
                codes.append(r.status_code)
            print("CODES_ZERO:", codes)
            assert codes == [200, 200, 200, 200, 200, 429], codes
    """))
    proc = subprocess.run(
        [sys.executable, str(probe)],
        cwd=tmp_path,
        env=_child_env(
            JWT_SECRET_KEY="test-only-secret-not-for-production",
            RATE_LIMIT_LOGIN="5/minute",
            RATE_LIMIT_PREDICT="1000/minute",
            RATE_LIMIT_EXPLAIN="1000/minute",
            TRUSTED_PROXY_HOPS="0",
        ),
        capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, "STDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr[-2000:]


def test_debug_client_ip_disabled_by_default(client):
    """The diagnostics endpoint must 404 unless explicitly enabled."""
    res = client.get("/_debug/client-ip")
    assert res.status_code == 404


def test_debug_client_ip_when_enabled(client, monkeypatch):
    """With the flag on: echoes raw XFF, peer, hops and resolved IP."""
    from src.core import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "DEBUG_CLIENT_IP", True)
    res = client.get("/_debug/client-ip",
                     headers={"X-Forwarded-For": "9.9.9.9, 10.0.0.7"})
    assert res.status_code == 200
    body = res.json()
    assert body["x_forwarded_for"] == "9.9.9.9, 10.0.0.7"
    assert body["peer"] == "testclient"
    assert body["trusted_proxy_hops"] == 1
    assert body["resolved_ip"] == "10.0.0.7"


def test_all_expected_routes_registered():
    """A dropped include_router (as happened with predict-explain during the
    EMI wiring) must fail loudly instead of 404ing in production."""
    from src.api.main import app

    def _iter_routes(routes):
        for route in routes:
            # Starlette 1.x mounts included routers as _IncludedRouter
            # (path None); the real APIRoutes live on .original_router.
            inner = getattr(route, "original_router", None)
            if inner is not None and hasattr(inner, "routes"):
                yield from _iter_routes(inner.routes)
                continue
            if hasattr(route, "path") and hasattr(route, "methods"):
                yield route

    paths = set()
    for route in _iter_routes(app.routes):
        for method in (route.methods or ()):
            if method in ("GET", "POST", "DELETE"):
                paths.add((method, route.path))
    for expected in [
        ("GET", "/"), ("POST", "/auth/signup"), ("POST", "/auth/login"),
        ("POST", "/predict"), ("POST", "/predict-explain"),
        ("POST", "/predict-explain-curve"), ("POST", "/emi"),
        ("GET", "/history"), ("GET", "/history/{app_id}"),
        ("DELETE", "/history/{app_id}"), ("DELETE", "/me/data"),
        ("GET", "/admin/stats"), ("GET", "/admin/users"), ("GET", "/admin/model"),
        ("GET", "/_debug/client-ip"),
    ]:
        assert expected in paths, f"route missing: {expected}"

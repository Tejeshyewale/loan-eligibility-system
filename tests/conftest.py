"""Shared fixtures: isolated in-memory test DB + TestClient (never touches loan.db)."""
import pytest
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
TestingSession = sessionmaker(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _test_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session():
    session = TestingSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db_session):
    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Signup + login, return Authorization headers (unique user per test)."""
    username = "user_%s" % str(id(object()))[-6:]
    client.post("/auth/signup", json={"username": username, "password": "secret123"})
    res = client.post("/auth/login", json={"username": username, "password": "secret123"})
    assert res.status_code == 200
    return {"Authorization": "Bearer " + res.json()["access_token"]}


STRONG_EXPLAIN_PAYLOAD = {
    "no_of_dependents": 0, "education": "Graduate", "self_employed": "No",
    "income_annum": 9000000, "loan_amount": 5000000, "loan_term": 12,
    "cibil_score": 800, "residential_assets_value": 5000000,
    "commercial_assets_value": 3000000, "luxury_assets_value": 4000000,
    "bank_asset_value": 3000000,
}

OOD_REJECT_PAYLOAD = {
    "no_of_dependents": 5, "education": "Not Graduate", "self_employed": "No",
    "income_annum": 200000, "loan_amount": 5000000, "loan_term": 12,
    "cibil_score": 300, "residential_assets_value": 100000,
    "commercial_assets_value": 0, "luxury_assets_value": 50000,
    "bank_asset_value": 50000,
}

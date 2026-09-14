"""Auth tests: signup + login against the isolated test DB."""


def test_signup_creates_user(client):
    res = client.post("/auth/signup", json={"username": "alice", "password": "pw123"})
    assert res.status_code == 200
    assert res.json()["message"] == "User created successfully"


def test_signup_duplicate_rejected(client):
    client.post("/auth/signup", json={"username": "bob", "password": "pw123"})
    res = client.post("/auth/signup", json={"username": "bob", "password": "pw123"})
    assert res.status_code == 400


def test_signup_missing_fields_rejected(client):
    res = client.post("/auth/signup", json={"username": "nobody"})
    assert res.status_code == 400


def test_login_valid_returns_token(client):
    client.post("/auth/signup", json={"username": "carol", "password": "pw123"})
    res = client.post("/auth/login", json={"username": "carol", "password": "pw123"})
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_rejected(client):
    client.post("/auth/signup", json={"username": "dave", "password": "pw123"})
    res = client.post("/auth/login", json={"username": "dave", "password": "wrong"})
    assert res.status_code == 401


def test_login_unknown_user_rejected(client):
    res = client.post("/auth/login", json={"username": "ghost", "password": "pw123"})
    assert res.status_code == 401

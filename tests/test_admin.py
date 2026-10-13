"""Admin endpoints: DB-backed role gate, stats shape, hash hygiene."""
import json


def _make_admin(client, db_session, username="admin_probe"):
    from src.api.auth import hash_password
    from src.database.models import User

    db_session.add(User(username=username, password=hash_password("secret123"),
                        role="admin"))
    db_session.commit()
    res = client.post("/auth/login", json={"username": username, "password": "secret123"})
    assert res.status_code == 200
    return {"Authorization": "Bearer " + res.json()["access_token"]}


def _seed_app(db_session, uid, prediction="Approved", prob=0.9):
    from src.database.models import LoanApplication
    row = LoanApplication(user_id=uid, input_data=json.dumps({}),
                          prediction=prediction, probability=prob,
                          model_version="model_v1", is_estimate=False,
                          top_reasons=json.dumps([]), suggestions=json.dumps([]))
    db_session.add(row)
    db_session.commit()
    return row


def test_normal_user_gets_403_everywhere(client, auth_headers):
    assert client.get("/admin/stats", headers=auth_headers).status_code == 403
    assert client.get("/admin/users", headers=auth_headers).status_code == 403
    assert client.get("/admin/model", headers=auth_headers).status_code == 403


def test_no_token_is_401_not_403(client):
    assert client.get("/admin/stats").status_code == 401


def test_demoted_admin_with_old_token_gets_403(client, db_session):
    from src.database.models import User

    headers = _make_admin(client, db_session, username="demote_me")
    assert client.get("/admin/stats", headers=headers).status_code == 200
    # Demote in DB while the JWT (still claiming admin) is live.
    db_session.query(User).filter(User.username == "demote_me").update({"role": "user"})
    db_session.commit()
    assert client.get("/admin/stats", headers=headers).status_code == 403
    assert client.get("/admin/users", headers=headers).status_code == 403


def test_admin_stats_users_model(client, db_session):
    from src.database.models import User

    headers = _make_admin(client, db_session, username="stats_boss")
    db_session.expire_all()
    boss_id = db_session.query(User).filter(User.username == "stats_boss").one().id
    _seed_app(db_session, boss_id, "Approved", 0.9)
    _seed_app(db_session, boss_id, "Rejected", 0.1)

    stats = client.get("/admin/stats", headers=headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["total_applications"] == 2
    assert body["approval_rate"] == 0.5
    assert body["avg_probability"] == 0.5
    assert body["applications_per_day"] and body["applications_per_day"][0]["count"] == 2
    assert body["model_version"] == "model_v1"

    users = client.get("/admin/users", headers=headers).json()["users"]
    assert users, "user list must not be empty"
    for entry in users:
        assert set(entry) == {"id", "username", "role", "applications"}
        assert "password" not in entry  # hashes must never leave the DB
    boss = [u for u in users if u["username"] == "stats_boss"][0]
    assert boss["role"] == "admin" and boss["applications"] == 2

    model = client.get("/admin/model", headers=headers)
    assert model.status_code == 200
    assert model.json()["model_version"] == "model_v1"

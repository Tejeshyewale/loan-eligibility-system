"""History endpoints: logging, pagination, ownership (IDOR), deletion."""
import json

from tests.test_shap_correctness import PROFILES_10

FIVE = {"income": 800000, "loan_amount": 300000, "cibil_score": 700,
        "bank_assets": 100000, "luxury_assets": 50000}


def _signup_login(client, username):
    assert client.post("/auth/signup",
                       json={"username": username, "password": "secret123"}).status_code == 200
    res = client.post("/auth/login", json={"username": username, "password": "secret123"})
    assert res.status_code == 200
    return {"Authorization": "Bearer " + res.json()["access_token"]}


def _user_id(db_session, username):
    from src.database.models import User
    db_session.expire_all()
    return db_session.query(User).filter(User.username == username).one().id


def _seed_row(db_session, uid, prediction="Approved", prob=0.8):
    from src.database.models import LoanApplication
    row = LoanApplication(user_id=uid, input_data=json.dumps({"cibil_score": 700}),
                          prediction=prediction, probability=prob,
                          model_version="model_v1", is_estimate=False,
                          top_reasons=json.dumps(["r1"]), suggestions=json.dumps(["s1"]))
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row.id


def test_explain_call_is_logged_and_listed(client, db_session):
    h = _signup_login(client, "history_logger")
    res = client.post("/predict-explain", json=PROFILES_10[2], headers=h)
    assert res.status_code == 200
    body = client.get("/history", headers=h)
    assert body.status_code == 200
    data = body.json()
    assert data["total"] == 1
    item = data["items"][0]  # newest first (only row for this user)
    assert item["prediction"] == res.json()["prediction"]
    assert item["probability"] == res.json()["probability"]
    assert item["is_estimate"] is False
    assert item["model_version"] == "model_v1"
    assert item["input_data"]["cibil_score"] == 700
    assert len(item["top_reasons"]) == 3 and len(item["suggestions"]) >= 1


def test_predict_call_logged_as_estimate(client):
    h = _signup_login(client, "history_estimator")
    client.post("/predict", json=FIVE, headers=h)
    items = client.get("/history", headers=h).json()["items"]
    assert items and items[0]["is_estimate"] is True
    assert set(items[0]["input_data"]) >= {"income_annum", "cibil_score"}


def test_history_pagination(client, db_session):
    h = _signup_login(client, "history_pager")
    me = _user_id(db_session, "history_pager")
    for _ in range(3):
        _seed_row(db_session, me)
    page1 = client.get("/history?limit=2&offset=0", headers=h).json()
    page2 = client.get("/history?limit=2&offset=2", headers=h).json()
    assert page1["total"] == 3 and len(page1["items"]) == 2
    assert len(page2["items"]) == 1
    ids1 = [i["id"] for i in page1["items"]]
    ids2 = [i["id"] for i in page2["items"]]
    assert not set(ids1) & set(ids2)
    assert ids1 == sorted(ids1, reverse=True)  # newest first
    assert client.get("/history?limit=0", headers=h).status_code == 422
    assert client.get("/history?limit=101", headers=h).status_code == 422


def test_get_single_item(client, db_session):
    h = _signup_login(client, "history_reader")
    rid = _seed_row(db_session, _user_id(db_session, "history_reader"))
    res = client.get(f"/history/{rid}", headers=h)
    assert res.status_code == 200
    assert res.json()["id"] == rid
    assert client.get("/history/999999", headers=h).status_code == 404


def test_idor_other_users_rows_are_invisible(client, db_session):
    ha = _signup_login(client, "history_alice")
    hb = _signup_login(client, "history_bob")
    aid, bid = _user_id(db_session, "history_alice"), _user_id(db_session, "history_bob")
    alice_row = _seed_row(db_session, aid, prediction="Rejected", prob=0.1)

    # Bob's list never contains Alice's row.
    blist = client.get("/history", headers=hb).json()
    assert all(i["id"] != alice_row for i in blist["items"])
    # Bob reads/deletes Alice's row -> 404, not 403, and row survives.
    assert client.get(f"/history/{alice_row}", headers=hb).status_code == 404
    assert client.delete(f"/history/{alice_row}", headers=hb).status_code == 404
    # Bob's delete-all only touches Bob's rows.
    bob_row = _seed_row(db_session, bid)
    assert client.delete("/me/data", headers=hb).status_code == 200
    assert client.get(f"/history/{alice_row}", headers=ha).status_code == 200
    assert client.get(f"/history/{bob_row}", headers=hb).status_code == 404
    # Alice deletes her own row -> gone.
    assert client.delete(f"/history/{alice_row}", headers=ha).status_code == 200
    assert client.get(f"/history/{alice_row}", headers=ha).status_code == 404


def test_history_requires_auth(client):
    assert client.get("/history").status_code == 401
    assert client.delete("/me/data").status_code == 401

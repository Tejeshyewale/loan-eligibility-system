"""Tests for the /predict quick-estimate endpoint (ML-backed)."""

VALID = {"income": 500000, "loan_amount": 200000, "cibil_score": 750,
         "bank_assets": 150000, "luxury_assets": 150000}


def test_predict_valid_baseline(client, auth_headers):
    res = client.post("/predict", json=VALID, headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["loan_approved"] is True
    assert body["estimate"] is True
    assert body["fallback"] is False
    assert body["probability"] is not None and 0.0 <= body["probability"] <= 1.0
    assert body["score"] == min(5, max(0, round(body["probability"] * 5)))
    assert set(body["assumed_defaults"]) == {
        "no_of_dependents", "education", "self_employed", "loan_term",
        "residential_assets_value", "commercial_assets_value",
    }


def test_heuristic_fallback_function_kept(client):
    """Legacy heuristic survives as a pure function for tests/fallback."""
    from src.api.predict import LoanRequest, heuristic_score

    approved, score = heuristic_score(LoanRequest(**VALID))
    assert (approved, score) == (True, 5)


def test_predict_rejected_profile(client, auth_headers):
    res = client.post("/predict", json={
        "income": 100000, "loan_amount": 400000, "cibil_score": 500,
        "bank_assets": 10000, "luxury_assets": 10000}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["loan_approved"] is False


def test_predict_negative_income_rejected(client, auth_headers):
    bad = dict(VALID, income=-1000)
    res = client.post("/predict", json=bad, headers=auth_headers)
    assert res.status_code == 422


def test_predict_missing_field_rejected(client, auth_headers):
    bad = dict(VALID)
    del bad["cibil_score"]
    res = client.post("/predict", json=bad, headers=auth_headers)
    assert res.status_code == 422


def test_predict_no_token_unauthorized(client):
    res = client.post("/predict", json=VALID)
    assert res.status_code == 401

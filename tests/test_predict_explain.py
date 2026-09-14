"""Tests for POST /predict-explain: response shape + auth enforcement."""
from .conftest import STRONG_EXPLAIN_PAYLOAD


def test_predict_explain_shape(client, auth_headers):
    res = client.post("/predict-explain", json=STRONG_EXPLAIN_PAYLOAD, headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"prediction", "probability", "top_reasons",
                         "reasons_detail", "suggestions"}
    assert body["prediction"] in ("Approved", "Rejected")
    assert 0.0 <= body["probability"] <= 1.0
    assert 1 <= len(body["top_reasons"]) <= 3
    assert all(isinstance(s, str) for s in body["top_reasons"])
    assert len(body["reasons_detail"]) == 5
    for item in body["reasons_detail"]:
        assert set(item) == {"feature", "shap_value", "direction"}
        assert item["direction"] in ("positive", "negative")
    assert 1 <= len(body["suggestions"]) <= 3


def test_predict_explain_no_token_unauthorized(client):
    res = client.post("/predict-explain", json=STRONG_EXPLAIN_PAYLOAD)
    assert res.status_code == 401

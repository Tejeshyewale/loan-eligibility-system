"""Unification tests: /predict (quick estimate) runs the SAME ML model as
/predict-explain, so identical 11-field inputs must give identical decisions.

Note on the 10 audit profiles: /predict fills 6 uncollected fields with
documented defaults, i.e. it evaluates a DIFFERENT 11-field vector than the
full form. Different inputs may legitimately yield different verdicts —
that is disclosed via estimate/assumed_defaults, not hidden. What must
hold exactly (tested below): same model + same inputs => same decision.
"""
import pytest

from config import config as _app_config

# (dependents, education, self_employed, income, loan, term,
#  cibil, residential, commercial, luxury, bank)
PROFILES = [
    (0, "Graduate", "No", 1500000, 200000, 5, 800, 2000000, 1000000, 500000, 800000),
    (4, "Not Graduate", "Yes", 200000, 900000, 20, 300, 0, 0, 0, 5000),
    (1, "Graduate", "No", 800000, 300000, 10, 700, 500000, 0, 50000, 100000),
    (2, "Graduate", "Yes", 600000, 500000, 15, 650, 300000, 100000, 200000, 50000),
    (0, "Not Graduate", "No", 400000, 100000, 5, 720, 100000, 0, 0, 150000),
    (3, "Graduate", "No", 500000, 400000, 10, 580, 200000, 0, 100000, 30000),
    (1, "Graduate", "No", 2000000, 1500000, 20, 750, 1000000, 500000, 300000, 200000),
    (5, "Not Graduate", "Yes", 300000, 200000, 10, 620, 50000, 0, 20000, 10000),
    (2, "Graduate", "No", 950000, 900000, 12, 690, 800000, 200000, 100000, 90000),
    (0, "Graduate", "No", 1200000, 100000, 3, 810, 500000, 0, 600000, 400000),
]

ELEVEN_KEYS = ("no_of_dependents", "education", "self_employed", "income_annum",
               "loan_amount", "loan_term", "cibil_score", "residential_assets_value",
               "commercial_assets_value", "luxury_assets_value", "bank_asset_value")


def _five_of(eleven):
    return {
        "income": eleven["income_annum"],
        "loan_amount": eleven["loan_amount"],
        "cibil_score": eleven["cibil_score"],
        "bank_assets": eleven["bank_asset_value"],
        "luxury_assets": eleven["luxury_assets_value"],
    }


@pytest.mark.parametrize("profile", PROFILES)
def test_predict_matches_explain_on_identical_inputs(client, auth_headers, profile):
    """Same 11 fields through both endpoints => same verdict, no fallback."""
    eleven = dict(zip(ELEVEN_KEYS, profile))
    quick = client.post("/predict", json=_five_of(eleven), headers=auth_headers)

    # Rebuild EXACTLY what /predict assumed: 5 real fields + 6 config defaults.
    q = _app_config.quick_estimate
    same_eleven = {
        **eleven,
        "no_of_dependents": q.no_of_dependents,
        "education": q.education,
        "self_employed": q.self_employed,
        "loan_term": q.loan_term,
        "residential_assets_value": q.residential_assets_value,
        "commercial_assets_value": q.commercial_assets_value,
    }
    full = client.post("/predict-explain", json=same_eleven, headers=auth_headers)
    assert quick.status_code == 200, quick.text
    assert full.status_code == 200, full.text
    assert quick.json()["fallback"] is False
    assert quick.json()["estimate"] is True
    assert quick.json()["loan_approved"] == (full.json()["prediction"] == "Approved")


def test_predict_discloses_assumed_defaults(client, auth_headers):
    """Transparency contract: every /predict response names its assumptions."""
    res = client.post("/predict", json={
        "income": 800000, "loan_amount": 300000, "cibil_score": 700,
        "bank_assets": 100000, "luxury_assets": 50000}, headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["estimate"] is True
    assert set(body["assumed_defaults"]) == {
        "no_of_dependents", "education", "self_employed", "loan_term",
        "residential_assets_value", "commercial_assets_value",
    }

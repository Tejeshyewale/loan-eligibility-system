"""SHAP correctness: additivity, sign convention, semantics, name alignment.

Regression net for the (1, 15, 2) misindexing bug (old code flattened and
truncated to class-0 values interleaved across features). See docs/SHAP_AUDIT.md.
"""
import numpy as np
import pandas as pd
import pytest

from src.core.explainability_engine import (
    RAW_FIELDS,
    _human_readable_name,
    _load_artifacts,
    _normalize_categoricals,
    explain_prediction,
)
from src.features.feature_engineering import create_features

PROFILES_10 = [
    {"no_of_dependents": 0, "education": "Graduate", "self_employed": "No",
     "income_annum": 1500000, "loan_amount": 200000, "loan_term": 5, "cibil_score": 800,
     "residential_assets_value": 2000000, "commercial_assets_value": 1000000,
     "luxury_assets_value": 500000, "bank_asset_value": 800000},
    {"no_of_dependents": 4, "education": "Not Graduate", "self_employed": "Yes",
     "income_annum": 200000, "loan_amount": 900000, "loan_term": 20, "cibil_score": 300,
     "residential_assets_value": 0, "commercial_assets_value": 0,
     "luxury_assets_value": 0, "bank_asset_value": 5000},
    {"no_of_dependents": 1, "education": "Graduate", "self_employed": "No",
     "income_annum": 800000, "loan_amount": 300000, "loan_term": 10, "cibil_score": 700,
     "residential_assets_value": 500000, "commercial_assets_value": 0,
     "luxury_assets_value": 50000, "bank_asset_value": 100000},
    {"no_of_dependents": 2, "education": "Graduate", "self_employed": "Yes",
     "income_annum": 600000, "loan_amount": 500000, "loan_term": 15, "cibil_score": 650,
     "residential_assets_value": 300000, "commercial_assets_value": 100000,
     "luxury_assets_value": 200000, "bank_asset_value": 50000},
    {"no_of_dependents": 0, "education": "Not Graduate", "self_employed": "No",
     "income_annum": 400000, "loan_amount": 100000, "loan_term": 5, "cibil_score": 720,
     "residential_assets_value": 100000, "commercial_assets_value": 0,
     "luxury_assets_value": 0, "bank_asset_value": 150000},
    {"no_of_dependents": 3, "education": "Graduate", "self_employed": "No",
     "income_annum": 500000, "loan_amount": 400000, "loan_term": 10, "cibil_score": 580,
     "residential_assets_value": 200000, "commercial_assets_value": 0,
     "luxury_assets_value": 100000, "bank_asset_value": 30000},
    {"no_of_dependents": 1, "education": "Graduate", "self_employed": "No",
     "income_annum": 2000000, "loan_amount": 1500000, "loan_term": 20, "cibil_score": 750,
     "residential_assets_value": 1000000, "commercial_assets_value": 500000,
     "luxury_assets_value": 300000, "bank_asset_value": 200000},
    {"no_of_dependents": 5, "education": "Not Graduate", "self_employed": "Yes",
     "income_annum": 300000, "loan_amount": 200000, "loan_term": 10, "cibil_score": 620,
     "residential_assets_value": 50000, "commercial_assets_value": 0,
     "luxury_assets_value": 20000, "bank_asset_value": 10000},
    {"no_of_dependents": 2, "education": "Graduate", "self_employed": "No",
     "income_annum": 950000, "loan_amount": 900000, "loan_term": 12, "cibil_score": 690,
     "residential_assets_value": 800000, "commercial_assets_value": 200000,
     "luxury_assets_value": 100000, "bank_asset_value": 90000},
    {"no_of_dependents": 0, "education": "Graduate", "self_employed": "No",
     "income_annum": 1200000, "loan_amount": 100000, "loan_term": 3, "cibil_score": 810,
     "residential_assets_value": 500000, "commercial_assets_value": 0,
     "luxury_assets_value": 600000, "bank_asset_value": 400000},
]


def _row(raw):
    norm = _normalize_categoricals(raw)
    df = create_features(pd.DataFrame([{k: norm[k] for k in RAW_FIELDS}]))
    return df


@pytest.mark.parametrize("raw", PROFILES_10)
def test_shap_additivity_rejected_class(raw):
    """expected_value[1] + sum(class-1 SHAP) == P(Rejected), tol 1e-4."""
    model, preprocessor, explainer = _load_artifacts()
    X = preprocessor.transform(_row(raw))
    sv = np.asarray(explainer.shap_values(X))
    assert sv.ndim == 3, f"unexpected SHAP shape {sv.shape}"
    class1 = sv[0, :, 1]
    proba_rejected = float(model.predict_proba(X)[0][1])
    base = float(np.asarray(explainer.expected_value).reshape(-1)[1])
    assert abs(base + class1.sum() - proba_rejected) < 1e-4


@pytest.mark.parametrize("raw", PROFILES_10)
def test_displayed_sign_convention(raw):
    """Displayed value = -(class-1 SHAP); positive means toward Approval.

    Mapping: class-1 SHAP explains P(Rejected), so negating flips the frame
    to P(Approved): displayed>0 pushes approval, displayed<0 pushes rejection.
    """
    model, preprocessor, explainer = _load_artifacts()
    X = preprocessor.transform(_row(raw))
    sv = np.asarray(explainer.shap_values(X))[0, :, 1]
    result = explain_prediction(dict(raw))
    by_encoded = {r["encoded_name"]: r for r in result["ranked"]}
    names = list(preprocessor.get_feature_names_out())
    assert len(result["ranked"]) == len(names)
    for fname, val in zip(names, -sv, strict=True):
        assert fname in by_encoded
        assert by_encoded[fname]["shap_value"] == pytest.approx(float(val))
        want_dir = "positive" if float(val) >= 0 else "negative"
        assert by_encoded[fname]["direction"] == want_dir


def test_feature_names_align_with_transformed_matrix():
    """Ranked encoded names must be exactly the preprocessor's output columns."""
    _, preprocessor, _ = _load_artifacts()
    names = [str(n) for n in preprocessor.get_feature_names_out()]
    result = explain_prediction(dict(PROFILES_10[2]))
    assert [r["encoded_name"] for r in result["ranked"]] != []
    assert sorted(r["encoded_name"] for r in result["ranked"]) == sorted(names)
    for r in result["ranked"]:
        assert r["feature_name"] == _human_readable_name(r["encoded_name"])


def test_low_cibil_semantics():
    """Very low CIBIL: flagged negatively by name + earns a CIBIL suggestion."""
    from src.core.reasoning_generator import generate_reasons
    from src.core.suggestion_engine import generate_suggestions

    result = explain_prediction(dict(PROFILES_10[1]))  # cibil 300
    assert result["prediction"] == "Rejected"
    negs = [r for r in result["ranked"] if r["direction"] == "negative"]
    assert any(r["feature_name"] == "cibil_score" for r in negs[:3]), \
        "cibil_score must be among top-3 negative reasons"
    reasons = generate_reasons(result["ranked"], result["prediction"])
    assert any("CIBIL" in s for s in reasons)
    tips = generate_suggestions(result["ranked"], PROFILES_10[1],
                                prediction="Rejected", probability=0.06)
    assert any("CIBIL" in t for t in tips)


def test_high_cibil_semantics():
    """High CIBIL + high income: CIBIL must NOT appear as a negative driver."""
    result = explain_prediction(dict(PROFILES_10[0]))  # cibil 800
    assert result["prediction"] == "Approved"
    negs = {r["feature_name"] for r in result["ranked"] if r["direction"] == "negative"}
    assert "cibil_score" not in negs

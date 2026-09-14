"""Unit tests for the SHAP explainability engine output structure."""
from src.core.explainability_engine import explain_prediction
from .conftest import OOD_REJECT_PAYLOAD, STRONG_EXPLAIN_PAYLOAD


def test_explain_structure_rejected():
    result = explain_prediction(dict(OOD_REJECT_PAYLOAD))
    assert result["prediction"] in ("Approved", "Rejected")
    assert 0.0 <= result["probability"] <= 1.0
    ranked = result["ranked"]
    assert isinstance(ranked, list) and len(ranked) > 0
    for item in ranked:
        assert set(item) >= {"feature_name", "shap_value", "direction"}
        assert isinstance(item["feature_name"], str)
        assert isinstance(item["shap_value"], float)
        assert item["direction"] in ("positive", "negative")
    magnitudes = [abs(item["shap_value"]) for item in ranked]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_explain_structure_approved():
    result = explain_prediction(dict(STRONG_EXPLAIN_PAYLOAD))
    assert result["prediction"] == "Approved"
    assert result["probability"] > 0.8

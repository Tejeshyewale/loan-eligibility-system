"""Regression lock for the Phase 1 OOD fix: CIBIL 300 + 25x leverage must stay Rejected."""
from src.core.explainability_engine import explain_prediction

from .conftest import OOD_REJECT_PAYLOAD


def test_ood_extreme_reject_stays_rejected():
    result = explain_prediction(dict(OOD_REJECT_PAYLOAD))
    assert result["prediction"] == "Rejected", (
        f"OOD blind spot regressed: expected Rejected, got {result['prediction']} "
        f"(p={result['probability']:.4f})")

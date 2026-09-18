from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Union

from src.api.auth import get_current_user
from src.api.rate_limit import limiter
from src.core.explainability_engine import (
    MAX_SWEEP_VALUES,
    SWEEPABLE_FIELDS,
    approval_probabilities,
    explain_prediction,
)
from src.core.reasoning_generator import generate_reasons
from src.core.suggestion_engine import generate_suggestions
from src.core.settings import RATE_LIMIT_EXPLAIN

router = APIRouter(tags=["Explainability"])


class ExplainRequest(BaseModel):
    no_of_dependents: int
    education: str
    self_employed: str
    income_annum: float
    loan_amount: float
    loan_term: float
    cibil_score: float
    residential_assets_value: float
    commercial_assets_value: float
    luxury_assets_value: float
    bank_asset_value: float


@router.post("/predict-explain")
@limiter.limit(RATE_LIMIT_EXPLAIN)
def predict_explain(request: Request, data: ExplainRequest, user: dict = Depends(get_current_user)):
    raw = data.model_dump()
    try:
        result = explain_prediction(raw)
    except RuntimeError as exc:
        # SHAP/numba unavailable on this host (e.g. blocked native DLL).
        raise HTTPException(status_code=503, detail=str(exc))
    top_reasons = generate_reasons(result["ranked"], result["prediction"])
    suggestions = generate_suggestions(
        result["ranked"], raw,
        prediction=result["prediction"], probability=result["probability"],
    )
    top_n = [
        {"feature": r["feature_name"], "shap_value": r["shap_value"], "direction": r["direction"]}
        for r in result["ranked"][:5]
    ]
    return {
        "prediction": result["prediction"],
        "probability": result["probability"],
        "top_reasons": top_reasons,
        "reasons_detail": top_n,
        "suggestions": suggestions,
    }


class CurveRequest(BaseModel):
    """What-If simulator: sweep one numeric field, keep the rest fixed."""
    base: ExplainRequest
    field: str
    values: list[float] = Field(min_length=1, max_length=MAX_SWEEP_VALUES)


@router.post("/predict-explain-curve")
@limiter.limit(RATE_LIMIT_EXPLAIN)
def predict_explain_curve(request: Request, data: CurveRequest, user: dict = Depends(get_current_user)):
    """Batch approval probabilities for a What-If sweep.

    Single transform + single predict_proba (no SHAP recompute) — one HTTP
    round-trip instead of N sequential /predict-explain calls.
    """
    if data.field not in SWEEPABLE_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"field must be one of {list(SWEEPABLE_FIELDS)}",
        )
    try:
        probs = approval_probabilities(data.base.model_dump(), data.field, data.values)
    except RuntimeError as exc:
        # SHAP/numba unavailable on this host (e.g. blocked native DLL).
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"field": data.field, "values": list(data.values), "probabilities": probs}

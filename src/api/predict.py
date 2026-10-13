"""Quick estimate endpoint: ML verdict from 5 fields.

Fills the 6 uncollected fields with documented defaults from
config.yaml (`quick_estimate`) and runs the same ML model as
/predict-explain, so both endpoints always agree. Every response carries
"estimate": true plus the assumed defaults for transparency.

If the model is unavailable, falls back to the legacy heuristic (with a
warning log + "fallback": true) rather than 500ing.
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from config import config as _app_config
from src.api.auth import get_current_user
from src.api.rate_limit import limiter
from src.core.explainability_engine import explain_prediction
from src.core.settings import RATE_LIMIT_PREDICT
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Prediction"])


class LoanRequest(BaseModel):
    income: float = Field(ge=0)
    loan_amount: float = Field(ge=0)
    cibil_score: int = Field(ge=300, le=900)
    bank_assets: float = Field(ge=0)
    luxury_assets: float = Field(ge=0)


def heuristic_score(data: LoanRequest) -> tuple:
    """Legacy 5-field heuristic (kept for tests + ML fallback only).

    Returns (approved, score_0_to_5). Do not use for new features.
    """
    score = 0

    if data.income >= 500000:
        score += 1
    if data.cibil_score >= 700:
        score += 1
    if data.bank_assets >= 100000:
        score += 1
    if data.luxury_assets >= 100000:
        score += 1
    if data.loan_amount <= data.income * 0.5:
        score += 1

    return score >= 3, score


def _ml_estimate(data: LoanRequest) -> dict:
    """Run the ML model on 5 real fields + 6 assumed defaults."""
    quick = _app_config.quick_estimate
    assumed = {
        "no_of_dependents": quick.no_of_dependents,
        "education": quick.education,
        "self_employed": quick.self_employed,
        "loan_term": quick.loan_term,
        "residential_assets_value": quick.residential_assets_value,
        "commercial_assets_value": quick.commercial_assets_value,
    }
    full_input = {
        "income_annum": data.income,
        "loan_amount": data.loan_amount,
        "cibil_score": data.cibil_score,
        "bank_asset_value": data.bank_assets,
        "luxury_assets_value": data.luxury_assets,
        **assumed,
    }
    result = explain_prediction(full_input)  # raises RuntimeError if shap blocked
    prob = float(result["probability"])
    approved = result["prediction"] == "Approved"
    # Backward-compatible 0-5 score, ML-derived and documented:
    # score = round(probability * 5), clamped to [0, 5].
    score = min(5, max(0, int(round(prob * 5))))
    return {
        "loan_approved": approved,
        "score": score,
        "probability": prob,
        "assumed_defaults": assumed,
    }


@router.post("/predict")
@limiter.limit(RATE_LIMIT_PREDICT)
def predict(request: Request, data: LoanRequest, user: dict = Depends(get_current_user)):
    try:
        est = _ml_estimate(data)
        fallback = False
    except Exception as exc:
        # Model unavailable (blocked shap, missing pickle, ...): degrade to
        # the legacy heuristic instead of failing the request.
        logger.warning("/predict ML unavailable, using heuristic fallback: %s", exc)
        approved, score = heuristic_score(data)
        est = {
            "loan_approved": approved,
            "score": score,
            "probability": None,
            "assumed_defaults": {},
        }
        fallback = True

    return {
        "applicant": user["username"],  # ✅ FIXED (no more sub)
        "loan_approved": est["loan_approved"],
        "score": est["score"],
        "criteria": {
            "Income": data.income,
            "Loan Amount": data.loan_amount,
            "CIBIL Score": data.cibil_score,
            "Bank Assets": data.bank_assets,
            "Luxury Assets": data.luxury_assets
        },
        "probability": est["probability"],
        "estimate": True,
        "assumed_defaults": est["assumed_defaults"],
        "fallback": fallback,
    }

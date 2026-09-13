from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Union

from src.api.auth import get_current_user
from src.core.explainability_engine import explain_prediction
from src.core.reasoning_generator import generate_reasons
from src.core.suggestion_engine import generate_suggestions

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
def predict_explain(data: ExplainRequest, user: dict = Depends(get_current_user)):
    raw = data.model_dump()
    result = explain_prediction(raw)
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

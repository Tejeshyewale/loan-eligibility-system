"""EMI calculator + affordability check. Auth is OPTIONAL so visitors can
explore; rate-limited per IP like other endpoints."""
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from config import config as _app_config
from src.api.rate_limit import limiter
from src.core.settings import RATE_LIMIT_PREDICT
from src.features.emi import (
    affordability_band,
    amortization_schedule,
    tenure_to_months,
    totals,
)

router = APIRouter(tags=["Financial tools"])


class EmiRequest(BaseModel):
    loan_amount: float = Field(gt=0, le=1_000_000_000)
    annual_rate_pct: float = Field(ge=0, le=100)
    tenure_value: int = Field(gt=0, le=50)
    tenure_unit: Literal["months", "years"] = "years"
    monthly_income: float | None = Field(default=None, ge=0)
    existing_emi: float = Field(default=0.0, ge=0)


_BAND_MESSAGE = {
    "ok": "Comfortable: total EMIs stay within the advised share of income.",
    "risky": "Risky: total EMIs take a large share of income — consider a smaller loan or longer tenure.",
    "not_advisable": "Not advisable: total EMIs exceed half the income.",
}


@router.post("/emi")
@limiter.limit(RATE_LIMIT_PREDICT)
def calculate_emi(request: Request, data: EmiRequest):
    months = tenure_to_months(data.tenure_value, data.tenure_unit)
    if months > 600:
        raise HTTPException(status_code=422, detail="Tenure too long (max 600 months).")
    summary = totals(data.loan_amount, data.annual_rate_pct, months)
    response = {
        "emi": summary["emi"],
        "total_interest": summary["total_interest"],
        "total_payment": summary["total_payment"],
        "tenure_months": months,
        "affordability": None,
        "schedule": amortization_schedule(data.loan_amount, data.annual_rate_pct, months),
    }
    if data.monthly_income:
        cfg = _app_config.affordability
        ratio = round((summary["emi"] + data.existing_emi) / data.monthly_income, 4)
        band = affordability_band(ratio, cfg.ok_max_ratio, cfg.risky_max_ratio)
        response["affordability"] = {
            "emi_to_income_ratio": ratio,
            "band": band,
            "message": _BAND_MESSAGE[band],
        }
    return response

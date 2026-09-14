from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.api.auth import get_current_user

router = APIRouter(tags=["Prediction"])


class LoanRequest(BaseModel):
    income: float = Field(ge=0)
    loan_amount: float = Field(ge=0)
    cibil_score: int = Field(ge=300, le=900)
    bank_assets: float = Field(ge=0)
    luxury_assets: float = Field(ge=0)


@router.post("/predict")
def predict(data: LoanRequest, user: dict = Depends(get_current_user)):
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

    approved = score >= 3

    return {
        "applicant": user["username"],  # ✅ FIXED (no more sub)
        "loan_approved": approved,
        "score": score,
        "criteria": {
            "Income": data.income,
            "Loan Amount": data.loan_amount,
            "CIBIL Score": data.cibil_score,
            "Bank Assets": data.bank_assets,
            "Luxury Assets": data.luxury_assets
        }
    }

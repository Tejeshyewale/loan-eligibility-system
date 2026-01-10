from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.auth import get_current_user

router = APIRouter(tags=["Prediction"])


class LoanRequest(BaseModel):
    income: float
    loan_amount: float
    cibil_score: int
    bank_assets: float
    luxury_assets: float


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

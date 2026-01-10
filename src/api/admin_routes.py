from fastapi import APIRouter, HTTPException
from src.database.db import SessionLocal
from src.database.models import LoanApplication

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/applications")
def get_applications():
    db = SessionLocal()
    apps = db.query(LoanApplication).all()
    db.close()
    return apps


@router.post("/approve/{app_id}")
def approve_application(app_id: int):
    db = SessionLocal()
    app = db.query(LoanApplication).get(app_id)

    if not app:
        db.close()
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = "Approved"
    db.commit()
    db.close()
    return {"message": "Application approved"}


@router.post("/reject/{app_id}")
def reject_application(app_id: int):
    db = SessionLocal()
    app = db.query(LoanApplication).get(app_id)

    if not app:
        db.close()
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = "Rejected"
    db.commit()
    db.close()
    return {"message": "Application rejected"}


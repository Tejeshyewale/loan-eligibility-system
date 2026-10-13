"""Per-user prediction history: log every prediction, browse/delete own rows.

Ownership rule: a row belonging to another user behaves as if it does not
exist (404, never 403) for read and delete; listings only ever return the
caller's rows.
"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.api.rate_limit import limiter
from src.core.settings import RATE_LIMIT_PREDICT
from src.database.db import get_db
from src.database.models import LoanApplication, User
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["History"])

MODEL_VERSION = "model_v1"
HISTORY_LIMIT_MAX = 100


def log_application(db: Session, user_id: int, input_data: dict,
                    prediction: str, probability: float, is_estimate: bool,
                    top_reasons: list, suggestions: list) -> None:
    """Best-effort history write. Raises nothing: callers must not break a
    prediction response because logging failed."""
    try:
        db.add(LoanApplication(
            user_id=user_id,
            created_at=datetime.utcnow(),
            input_data=json.dumps(input_data),
            prediction=prediction,
            probability=(None if probability is None else float(probability)),
            model_version=MODEL_VERSION,
            is_estimate=bool(is_estimate),
            top_reasons=json.dumps(top_reasons or []),
            suggestions=json.dumps(suggestions or []),
        ))
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("History logging failed (response unaffected): %s", exc)


def _current_user_id(db: Session, user: dict) -> int:
    row = db.query(User).filter(User.username == user["username"]).first()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return row.id


def resolve_user_id(db: Session, user: dict) -> int:
    """Public helper for other routes: JWT username -> users.id."""
    return _current_user_id(db, user)


def _serialize(app: LoanApplication) -> dict:
    return {
        "id": app.id,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "prediction": app.prediction,
        "probability": app.probability,
        "model_version": app.model_version,
        "is_estimate": bool(app.is_estimate),
        "input_data": json.loads(app.input_data),
        "top_reasons": json.loads(app.top_reasons),
        "suggestions": json.loads(app.suggestions),
    }


@router.get("/history")
@limiter.limit(RATE_LIMIT_PREDICT)
def list_history(request: Request, user: dict = Depends(get_current_user),
                 db: Session = Depends(get_db),
                 limit: int = Query(default=20, ge=1, le=HISTORY_LIMIT_MAX),
                 offset: int = Query(default=0, ge=0)):
    """Newest-first page of the caller's own applications."""
    uid = _current_user_id(db, user)
    rows = (db.query(LoanApplication)
            .filter(LoanApplication.user_id == uid)
            .order_by(LoanApplication.id.desc())
            .offset(offset).limit(limit).all())
    total = db.query(LoanApplication).filter(LoanApplication.user_id == uid).count()
    return {"total": total, "limit": limit, "offset": offset,
            "items": [_serialize(r) for r in rows]}


@router.get("/history/{app_id}")
@limiter.limit(RATE_LIMIT_PREDICT)
def get_history_item(request: Request, app_id: int,
                     user: dict = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    uid = _current_user_id(db, user)
    row = (db.query(LoanApplication)
           .filter(LoanApplication.id == app_id,
                   LoanApplication.user_id == uid).first())
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return _serialize(row)


@router.delete("/history/{app_id}")
@limiter.limit(RATE_LIMIT_PREDICT)
def delete_history_item(request: Request, app_id: int,
                        user: dict = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    uid = _current_user_id(db, user)
    row = (db.query(LoanApplication)
           .filter(LoanApplication.id == app_id,
                   LoanApplication.user_id == uid).first())
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(row)
    db.commit()
    return {"message": "Application deleted"}


@router.delete("/me/data")
@limiter.limit(RATE_LIMIT_PREDICT)
def delete_all_my_data(request: Request, user: dict = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """Delete every application row belonging to the caller (account kept)."""
    uid = _current_user_id(db, user)
    count = (db.query(LoanApplication)
             .filter(LoanApplication.user_id == uid).delete())
    db.commit()
    return {"message": f"Deleted {count} application(s)"}

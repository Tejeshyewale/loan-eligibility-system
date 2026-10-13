"""Admin API: portfolio stats, user list, model version.

Every route re-reads the caller's role from the DATABASE on each request —
a JWT carrying role="admin" is not sufficient (demote-then-reuse must 403).
"""
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.api.rate_limit import limiter
from src.api.routes.history import MODEL_VERSION
from src.core.settings import RATE_LIMIT_PREDICT
from src.database.db import get_db
from src.database.models import LoanApplication, User

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(request: Request, user: dict = Depends(get_current_user),
                  db: Session = Depends(get_db)) -> dict:
    """Gate: role comes from the users table, never from the JWT claim."""
    row = db.query(User).filter(User.username == user["username"]).first()
    if row is None or row.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"id": row.id, "username": row.username, "role": row.role}


@router.get("/stats")
@limiter.limit(RATE_LIMIT_PREDICT)
def admin_stats(request: Request, admin: dict = Depends(require_admin),
                db: Session = Depends(get_db)):
    rows = db.query(LoanApplication.prediction, LoanApplication.probability,
                    LoanApplication.created_at).all()
    total = len(rows)
    approved = sum(1 for r in rows if r[0] == "Approved")
    probs = [r[1] for r in rows if r[1] is not None]
    per_day = sorted(Counter(
        (r[2].date().isoformat() if isinstance(r[2], datetime) else str(r[2]))
        for r in rows
    ).items())
    return {
        "total_applications": total,
        "approval_rate": (approved / total) if total else None,
        "avg_probability": (sum(probs) / len(probs)) if probs else None,
        "applications_per_day": [{"date": d, "count": c} for d, c in per_day],
        "model_version": MODEL_VERSION,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/users")
@limiter.limit(RATE_LIMIT_PREDICT)
def admin_users(request: Request, admin: dict = Depends(require_admin),
                db: Session = Depends(get_db)):
    """User list — id/username/role/application count. Password hashes are
    never selected, let alone returned."""
    counts = dict(db.query(LoanApplication.user_id,
                           func.count(LoanApplication.id))
                  .group_by(LoanApplication.user_id).all())
    return {"users": [
        {"id": u.id, "username": u.username, "role": u.role,
         "applications": counts.get(u.id, 0)}
        for u in db.query(User).order_by(User.id).all()
    ]}


@router.get("/model")
@limiter.limit(RATE_LIMIT_PREDICT)
def admin_model(request: Request, admin: dict = Depends(require_admin)):
    return {"model_version": MODEL_VERSION,
            "notes": "See MODEL_CARD.md for data, limitations and intended use."}

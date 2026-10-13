from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.api.auth import (
    create_token,
    hash_password,
    verify_legacy_sha256,
    verify_password,
)
from src.api.rate_limit import limiter
from src.core.settings import RATE_LIMIT_LOGIN
from src.database.db import get_db
from src.database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup")
def signup(data: dict, db: Session = Depends(get_db)):
    username = data.get("username")
    password = data.get("password")
    # SECURITY: role is always "user" here. Any "role" key in the request
    # body is ignored — admins are created via create_admin.py only.
    # (Previously the body role was honored: privilege escalation.)

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username & password required")

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        username=username,
        password=hash_password(password),
        role="user",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully"}


@router.post("/login")
@limiter.limit(RATE_LIMIT_LOGIN)
def login(request: Request, data: dict, db: Session = Depends(get_db)):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username & password required")

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    password_ok = verify_password(password, user.password)
    if not password_ok and verify_legacy_sha256(password, user.password):
        # Transparent upgrade: correct legacy SHA-256 password -> rehash
        # with bcrypt so the weak hash disappears on first successful login.
        user.password = hash_password(password)
        db.commit()
        password_ok = True

    if not password_ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.username, user.role)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role
    }

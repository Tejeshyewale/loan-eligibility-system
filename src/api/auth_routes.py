from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
from src.api.auth import hash_password, verify_password, create_token
from src.api.rate_limit import limiter
from src.core.settings import RATE_LIMIT_LOGIN

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup")
def signup(data: dict, db: Session = Depends(get_db)):
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username & password required")

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        username=username,
        password=hash_password(password),
        role=role
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

    if not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.username, user.role)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role
    }

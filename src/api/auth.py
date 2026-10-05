import bcrypt
import hashlib
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.core.settings import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return False (not an error) for legacy pre-bcrypt hashes.

    MIGRATION NOTE: passwords stored before this change are unsalted SHA-256
    hex digests, which bcrypt rejects. Existing users in loan.db must reset
    their password (re-signup); they will get 401 until they do.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def is_legacy_sha256_hash(stored: str) -> bool:
    """Detect pre-bcrypt unsalted SHA-256 hex digests (64 hex chars)."""
    return (
        isinstance(stored, str)
        and len(stored) == 64
        and all(c in "0123456789abcdef" for c in stored.lower())
    )


def verify_legacy_sha256(plain_password: str, stored: str) -> bool:
    """Check a password against a legacy unsalted SHA-256 hex digest."""
    if not is_legacy_sha256_hash(stored):
        return False
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest() == stored.lower()


def create_token(username: str, role: str):
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# ✅ THIS WAS MISSING — NOW FIXED
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        return {
            "username": username,
            "role": role
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

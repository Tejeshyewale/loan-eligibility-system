"""Central app settings loaded from .env. Fails fast if required vars are missing."""
import os

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"[settings] Missing required environment variable '{name}'. "
            f"Copy .env.example to .env and set a value."
        )
    return value


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        raise RuntimeError(
            f"[settings] Environment variable '{name}' must be an integer."
        )


# --- Auth (required: app refuses to start without a real secret) ---
JWT_SECRET_KEY = _required("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = _int("ACCESS_TOKEN_EXPIRE_MINUTES", 60)

# --- CORS (comma-separated; no wildcard allowed with credentials) ---
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8501").split(",")
    if origin.strip()
]

# --- Rate limits (slowapi format; overridable per environment) ---
RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "5/minute")
RATE_LIMIT_PREDICT = os.getenv("RATE_LIMIT_PREDICT", "10/minute")
RATE_LIMIT_EXPLAIN = os.getenv("RATE_LIMIT_EXPLAIN", "10/minute")

"""Central app settings (pydantic-settings, loaded from .env).

Fails fast: JWT_SECRET_KEY has no default, so importing this module without
a real secret raises immediately instead of booting an insecure app.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Auth (required: no default -> ValidationError if missing) ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./loan.db"

    # --- CORS (comma-separated; no wildcard allowed with credentials) ---
    CORS_ALLOWED_ORIGINS: str = "http://localhost:8501"

    # --- Rate limits (slowapi format; overridable per environment) ---
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_PREDICT: str = "10/minute"
    RATE_LIMIT_EXPLAIN: str = "10/minute"

    # --- Bootstrap admin (optional; used by src/database/create_admin.py) ---
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""


settings = Settings()

# Module-level names (kept so existing `from src.core.settings import X`
# imports keep working unchanged).
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
DATABASE_URL = settings.DATABASE_URL
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
    if origin.strip()
]
RATE_LIMIT_LOGIN = settings.RATE_LIMIT_LOGIN
RATE_LIMIT_PREDICT = settings.RATE_LIMIT_PREDICT
RATE_LIMIT_EXPLAIN = settings.RATE_LIMIT_EXPLAIN
ADMIN_EMAIL = settings.ADMIN_EMAIL
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

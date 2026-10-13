import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api.auth_routes import router as auth_router
from src.api.debug import router as debug_router
from src.api.predict import router as predict_router
from src.api.rate_limit import limiter
from src.api.routes.emi import router as emi_router
from src.api.routes.history import router as history_router
from src.api.routes.predict_explain import router as predict_explain_router
from src.core.settings import CORS_ALLOWED_ORIGINS
from src.database.db import engine
from src.database.models import Base
from src.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure tables exist on startup (idempotent).

    This is the fallback path for sqlite/tests. On Render, migrations run
    first via `alembic upgrade head` in startCommand; create_all is then a
    harmless no-op. `engine` is read from module globals so tests can point
    it at an empty scratch DB."""
    if engine.url.get_backend_name() == "sqlite":
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured (sqlite fallback).")
    yield


app = FastAPI(title="Loan Eligibility API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Last-resort 500: log the traceback server-side, never leak it."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info("%s %s -> %s (%.1f ms)",
                    request.method, request.url.path,
                    response.status_code, elapsed_ms)
        return response
    except Exception:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.exception("%s %s failed after %.1f ms",
                         request.method, request.url.path, elapsed_ms)
        raise

# CORS: explicit origins from .env (never "*" with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "API running"}

app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(emi_router)
app.include_router(history_router)
app.include_router(debug_router)

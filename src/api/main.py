from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api.auth_routes import router as auth_router
from src.api.predict import router as predict_router
from src.api.routes.predict_explain import router as predict_explain_router
from src.api.rate_limit import limiter
from src.core.settings import CORS_ALLOWED_ORIGINS

app = FastAPI(title="Loan Eligibility API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(predict_explain_router)

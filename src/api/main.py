from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth_routes import router as auth_router
from src.api.predict import router as predict_router
from src.api.routes.predict_explain import router as predict_explain_router

app = FastAPI(title="Loan Eligibility API")

# CORS (IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)


class LoanApplication(Base):
    """One logged prediction per row. input_data/top_reasons/suggestions are
    JSON-encoded text so the schema stays stable across UI changes."""
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    input_data = Column(Text, nullable=False)
    prediction = Column(String, nullable=False)  # "Approved" | "Rejected"
    probability = Column(Float, nullable=True)  # None when the ML model was
    # unavailable and the heuristic fallback answered instead.
    model_version = Column(String, nullable=False, default="model_v1")
    is_estimate = Column(Boolean, nullable=False, default=False)  # True = /predict defaults
    top_reasons = Column(Text, nullable=False, default="[]")
    suggestions = Column(Text, nullable=False, default="[]")


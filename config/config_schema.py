"""Pydantic schema + validation for config/config.yaml.

Importing this module does NOT do I/O by itself; call load_config() or use
the singleton in config/__init__.py. Validation fails fast with a clear
error if a required key is missing or has the wrong type.
"""
import os

import yaml
from pydantic import BaseModel, ValidationError


class SuggestionEngineConfig(BaseModel):
    cibil_good_threshold: int
    cibil_min_threshold: int
    max_loan_income_ratio: float
    min_asset_loan_ratio: float
    min_bank_asset_value: int
    min_total_assets: int
    strong_approval_threshold: float
    max_suggestions: int


class HeuristicPredictConfig(BaseModel):
    min_income: float
    min_cibil_score: int
    min_bank_assets: float
    min_luxury_assets: float
    max_loan_income_ratio: float
    approval_min_score: int


class AppConfig(BaseModel):
    suggestion_engine: SuggestionEngineConfig
    heuristic_predict: HeuristicPredictConfig


DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def load_config(path: str = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load config.yaml and validate it. Raises a clear error on failure."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[config] Config file not found at '{path}'. "
            f"Expected config/config.yaml to exist with all required thresholds."
        )
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError(
            f"[config] Invalid config file at '{path}': "
            f"expected a YAML mapping with 'suggestion_engine' and 'heuristic_predict' sections."
        )
    try:
        return AppConfig.model_validate(raw)
    except ValidationError as e:
        # Re-raise with file context so startup failures are easy to diagnose.
        raise ValueError(
            f"[config] Config validation failed for '{path}'. "
            f"A required key is missing or has the wrong type.\n{e}"
        ) from e

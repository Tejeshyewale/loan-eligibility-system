"""One-time fix: rebuild models/preprocessor.pkl with debt_to_income_ratio included.

The committed preprocessor.pkl was stale (14 features) while models/model_v1.pkl
expects 15 features. Run once from the repo root:

    python scripts/fix_preprocessor.py
"""
import os
import pickle
import shutil

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.features.feature_engineering import create_features
from src.utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "validated", "clean_loan_data.csv")
PREPROCESSOR_PATH = os.path.join(BASE_DIR, "models", "preprocessor.pkl")
MODEL_PATH = os.path.join(BASE_DIR, "models", "model_v1.pkl")

NUMERIC_FEATURES = [
    'no_of_dependents', 'income_annum', 'loan_amount', 'loan_term', 'cibil_score',
    'residential_assets_value', 'commercial_assets_value', 'luxury_assets_value',
    'bank_asset_value', 'total_assets', 'loan_income_ratio', 'asset_loan_ratio',
    'debt_to_income_ratio',
]
CATEGORICAL_FEATURES = ['education', 'self_employed']


def main():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    df = create_features(df)
    X = df.drop(columns=["loan_status", "loan_id"], errors="ignore")

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline(steps=[('scaler', StandardScaler())]), NUMERIC_FEATURES),
            ('cat', Pipeline(steps=[('encoder', OneHotEncoder(drop='first', handle_unknown='ignore'))]), CATEGORICAL_FEATURES),
        ],
        remainder='drop',
    )
    preprocessor.fit(X)

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    n_expected = int(getattr(model, "n_features_in_", 0) or 0)
    n_actual = len(list(preprocessor.get_feature_names_out()))
    assert n_expected == n_actual, f"mismatch after rebuild: model={n_expected} preprocessor={n_actual}"
    logger.info(f"OK: model expects {n_expected}, rebuilt preprocessor has {n_actual}")

    backup = PREPROCESSOR_PATH + ".bak"
    shutil.copy2(PREPROCESSOR_PATH, backup)
    with open(PREPROCESSOR_PATH, "wb") as f:
        pickle.dump(preprocessor, f)
    logger.info(f"Overwrote {PREPROCESSOR_PATH} (backup at {backup})")
    logger.info("Features: %s", list(preprocessor.get_feature_names_out()))


if __name__ == "__main__":
    main()

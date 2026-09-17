"""Phase 2: SHAP-based explainability engine (additive, does not touch /predict)."""
import os
import pickle
from functools import lru_cache

import pandas as pd

from src.features.feature_engineering import create_features

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model_v1.pkl")
PREPROCESSOR_PATH = os.path.join(BASE_DIR, "models", "preprocessor.pkl")

# Raw fields the trained model needs (11 inputs; engineered features derived).
RAW_FIELDS = [
    "no_of_dependents", "education", "self_employed", "income_annum",
    "loan_amount", "loan_term", "cibil_score", "residential_assets_value",
    "commercial_assets_value", "luxury_assets_value", "bank_asset_value",
]


@lru_cache(maxsize=1)
def _load_artifacts():
    # NOTE: `shap` (via numba) ships native DLLs that can be blocked by
    # Windows Application Control policies on some hosts. Import it lazily so
    # a blocked/broken shap install breaks only /predict-explain at request
    # time — never the whole API at startup.
    try:
        import shap
    except ImportError as exc:
        raise RuntimeError(
            "SHAP explainability is unavailable on this host: the 'shap'/'numba' "
            f"native libraries failed to import ({exc}). Auth, /predict and /docs "
            "are unaffected; allowlist numba's DLLs or run /predict-explain "
            "elsewhere to restore explanations."
        ) from exc
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(PREPROCESSOR_PATH, "rb") as f:
        preprocessor = pickle.load(f)
    explainer = shap.TreeExplainer(model)
    return model, preprocessor, explainer


def _normalize_categoricals(raw_input: dict) -> dict:
    """Accept 'Graduate' or ' Graduate'; map to training format (' Graduate')."""
    out = dict(raw_input)
    for col, valid in (("education", [" Graduate", " Not Graduate"]),
                       ("self_employed", [" Yes", " No"])):
        v = out.get(col)
        if isinstance(v, str):
            s = v.strip().lower()
            for cand in valid:
                if cand.strip().lower() == s:
                    out[col] = cand
                    break
    return out


def _human_readable_name(encoded_name: str) -> str:
    """Map one-hot/scaled names back to original names.

    e.g. 'cat__encoder__education_Graduate' -> 'education',
         'num__cibil_score' -> 'cibil_score',
         'cat__education_ Not Graduate' -> 'education'.
    """
    name = encoded_name
    # Drop transformer prefix: 'num__x' / 'cat__...' (also handles 'cat__encoder__...')
    if "__" in name:
        name = name.split("__", 1)[1]
        # handle double prefix like 'encoder__education_Graduate'
        if "__" in name and name.split("__")[0].lower() in ("encoder", "scaler", "onehotencoder"):
            name = name.split("__", 1)[1]
    # One-hot remainder: 'education_Graduate' / 'education_ Not Graduate' -> 'education'
    for col in ("education", "self_employed"):
        if name == col or name.startswith(col + "_"):
            return col
    return name.strip()


def explain_prediction(raw_input: dict) -> dict:
    """Transform raw input, predict with the trained tree-based model, compute SHAP values.

    Returns dict with prediction, probability and ranked (feature, shap, direction).
    """
    model, preprocessor, explainer = _load_artifacts()

    raw_input = _normalize_categoricals(raw_input)
    df = pd.DataFrame([{k: raw_input[k] for k in RAW_FIELDS}])
    df = create_features(df)

    X_processed = preprocessor.transform(df)
    try:
        feature_names = list(preprocessor.get_feature_names_out())
    except Exception:
        feature_names = [f"feature_{i}" for i in range(X_processed.shape[1])]

    pred = int(model.predict(X_processed)[0])
    # LabelEncoder sorts classes alphabetically: Approved=0, Rejected=1,
    # so proba[:,1] is P(Rejected). Expose approval probability instead.
    proba_rejected = float(model.predict_proba(X_processed)[0][1])
    proba = 1.0 - proba_rejected

    shap_values = explainer.shap_values(X_processed)
    # TreeExplainer may return list (binary) or 2D array; take class-1 / single row.
    import numpy as np
    sv = shap_values
    if isinstance(sv, list):
        sv = sv[1] if len(sv) > 1 else sv[0]
    sv = np.asarray(sv)
    if sv.ndim == 2:
        sv = sv[0]
    sv = sv.reshape(-1)
    # SHAP values explain P(Rejected); negate so positive = towards approval.
    sv = -sv

    ranked = []
    for fname, val in zip(feature_names, sv):
        v = float(val)
        ranked.append({
            "feature_name": _human_readable_name(str(fname)),
            "encoded_name": str(fname),
            "shap_value": v,
            "direction": "positive" if v >= 0 else "negative",
        })
    ranked.sort(key=lambda r: abs(r["shap_value"]), reverse=True)

    return {
        "prediction": "Approved" if pred == 0 else "Rejected",
        "label": pred,
        "probability": proba,
        "ranked": ranked,
    }

"""Model-honesty tripwires: catch synthetic/separable data and unprovenanced metrics.

Background (docs/ML_AUDIT.md): the demo dataset is rule-generated — a
depth-3 tree scores 1.0 on holdout. These tests make that fact load-bearing:
retraining on real data should flip the separability test from xfail to
pass, and metrics.json must always carry its provenance.
"""
import hashlib
import json

import pytest

from config import config as _app_config


def _load_frame():
    import pandas as pd
    from sklearn.preprocessing import LabelEncoder

    df = pd.read_csv("data/validated/clean_loan_data.csv")
    df.columns = df.columns.str.strip()
    y = LabelEncoder().fit_transform(df["loan_status"])
    return df, y


def test_separable_data_tripwire():
    """A depth-3 tree must NOT ace holdout — unless demo data is allowed.

    allow_separable_data=true (demo dataset) turns a >0.99 score into an
    xfail with this message instead of a silent green build.
    """
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import StratifiedShuffleSplit
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.tree import DecisionTreeClassifier

    from src.features.feature_engineering import create_features

    df, y = _load_frame()
    frame = create_features(df.copy())
    X = frame.drop(columns=["loan_status", "loan_id"], errors="ignore")
    num = X.select_dtypes(include=[np.number]).columns
    Xv = X.copy()
    Xv[num] = StandardScaler().fit(Xv[num]).transform(Xv[num])
    cat = [c for c in ("education", "self_employed") if c in Xv.columns]
    Xv = pd.get_dummies(Xv, columns=cat, drop_first=True)
    y_enc = LabelEncoder().fit_transform(df["loan_status"])
    tr, te = next(StratifiedShuffleSplit(n_splits=1, test_size=0.2,
                                         random_state=7).split(Xv, y_enc))
    score = DecisionTreeClassifier(max_depth=3, random_state=0).fit(
        Xv.iloc[tr], y_enc[tr]).score(Xv.iloc[te], y_enc[te])
    if score > 0.99:
        if _app_config.model_governance.allow_separable_data:
            pytest.xfail(
                f"Demo data is synthetically separable (depth-3 tree: {score:.4f}). "
                "Set model_governance.allow_separable_data=false once training "
                "on real data so this becomes a hard failure.")
        pytest.fail(
            f"Data looks synthetically separable (depth-3 tree: {score:.4f}) "
            "but allow_separable_data is false.")


def test_metrics_json_has_provenance():
    """metrics.json must record data hash, seed, library versions and date."""
    with open("models/metrics.json", encoding="utf-8") as f:
        payload = json.load(f)
    assert "best_model" in payload and "metrics" in payload  # original content intact
    prov = payload.get("provenance")
    assert isinstance(prov, dict), "metrics.json lacks a 'provenance' block"
    digest = prov.get("data_sha256", "")
    assert isinstance(digest, str) and len(digest) == 64 \
        and all(c in "0123456789abcdef" for c in digest)
    assert isinstance(prov.get("seed"), int)
    assert isinstance(prov.get("date"), str) and prov["date"]
    libs = prov.get("library_versions")
    assert isinstance(libs, dict) and libs
    # The recorded data hash must match the actual training CSV.
    with open("data/validated/clean_loan_data.csv", "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    assert digest == actual, "metrics.json data_sha256 does not match clean_loan_data.csv"

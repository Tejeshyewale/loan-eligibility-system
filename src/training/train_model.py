import pandas as pd
import pickle
import os
import json
import xgboost as xgb

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from src.features.feature_engineering import create_features
 
from imblearn.over_sampling import SMOTE

# Paths
DATA_PATH = "data/validated/clean_loan_data.csv"
PREPROCESSOR_PATH = "models/preprocessor.pkl"
MODEL_PATH = "models/model_v1.pkl"
METRICS_PATH = "models/metrics.json"

def load_data():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    return df

def load_preprocessor():
    with open(PREPROCESSOR_PATH, "rb") as f:
        return pickle.load(f)

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

def prepare_data(df):
    # Recreate engineered features
    df = create_features(df)

    X = df.drop(columns=["loan_status", "loan_id"], errors='ignore')
    y_raw = df["loan_status"]

    # Encode target to 0/1 for XGBoost
    le = LabelEncoder()
    y = le.fit_transform(y_raw)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    numeric_features = [
        'no_of_dependents', 'income_annum', 'loan_amount', 'loan_term', 'cibil_score', 
        'residential_assets_value', 'commercial_assets_value', 'luxury_assets_value', 
        'bank_asset_value', 'total_assets', 'loan_income_ratio', 'asset_loan_ratio', 
        'debt_to_income_ratio'
    ]
    categorical_features = ['education', 'self_employed']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline(steps=[('scaler', StandardScaler())]), numeric_features),
            ('cat', Pipeline(steps=[('encoder', OneHotEncoder(drop='first', handle_unknown='ignore'))]), categorical_features)
        ],
        remainder='drop'
    )

    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)

    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train_processed, y_train)

    return X_train_res, X_test_processed, y_train_res, y_test, preprocessor

def evaluate_model(model, X_test, y_test):

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist()
    }
    return metrics

def main():
    print("STEP 6: Model Training Started")

    df = load_data()
    # preprocessor is now built dynamically in prepare_data

    X_train, X_test, y_train, y_test, preprocessor = prepare_data(df)

    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForest": RandomForestClassifier(n_estimators=200, random_state=42),
        "XGBoost": xgb.XGBClassifier(n_estimators=150, learning_rate=0.05, max_depth=3, use_label_encoder=False, eval_metric='logloss')
    }

    all_metrics = {}

    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        all_metrics[name] = metrics
        print(f"{name} ROC-AUC: {metrics['roc_auc']:.4f}")

    best_model_name = max(all_metrics, key=lambda k: all_metrics[k]["roc_auc"])
    best_model = models[best_model_name]
    best_metrics = all_metrics[best_model_name]

    print(f"\nBest Model: {best_model_name}")

    os.makedirs("models", exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(best_model, f)
        
    # Save the updated preprocessor
    with open(PREPROCESSOR_PATH, "wb") as f:
        pickle.dump(preprocessor, f)
        
    with open(METRICS_PATH, "w") as f:
        json.dump({
            "best_model": best_model_name,
            "metrics": best_metrics
        }, f, indent=4)

    # Save all metrics for the notebook to use, if desired.
    with open("models/all_metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=4)

    print("Best model trained & saved")
    print("STEP 6 COMPLETED")

if __name__ == "__main__":
    main()

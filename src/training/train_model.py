import pandas as pd
import pickle
import os

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score, matthews_corrcoef
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from src.features.feature_engineering import create_features
 
from imblearn.over_sampling import SMOTE

# Paths
DATA_PATH = "data/validated/clean_loan_data.csv"
PREPROCESSOR_PATH = "models/preprocessor.pkl"
MODEL_PATH = "models/gb_model.pkl"

def load_data():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    return df

def load_preprocessor():
    with open(PREPROCESSOR_PATH, "rb") as f:
        return pickle.load(f)

def prepare_data(df, preprocessor):
    # 🔑 Recreate engineered features
    df = create_features(df)

    X = df.drop(columns=["loan_status"])
    y = df["loan_status"]

    X_processed = preprocessor.transform(X)

    smote = SMOTE(random_state=42)
    X_res, y_res = smote.fit_resample(X_processed, y)

    return X_res, y_res

def train_and_evaluate(model, X, y):
    roc_scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")
    return roc_scores.mean()

def main():
    print("🚀 STEP 6: Model Training Started")

    df = load_data()
    preprocessor = load_preprocessor()

    X, y = prepare_data(df, preprocessor)

    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForest": RandomForestClassifier(n_estimators=200, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=150, learning_rate=0.05, max_depth=3
        )
    }

    results = {}

    for name, model in models.items():
        score = train_and_evaluate(model, X, y)
        results[name] = score
        print(f"{name} ROC-AUC: {score:.4f}")

    best_model_name = max(results, key=results.get)
    best_model = models[best_model_name]

    print(f"\n🏆 Best Model: {best_model_name}")

    best_model.fit(X, y)

    os.makedirs("models", exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(best_model, f)

    print("✅ Best model trained & saved")
    print("🎉 STEP 6 COMPLETED")

if __name__ == "__main__":
    main()


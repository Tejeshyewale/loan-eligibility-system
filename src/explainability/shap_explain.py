import pandas as pd
import pickle
import matplotlib.pyplot as plt
import numpy as np

from src.features.feature_engineering import create_features

DATA_PATH = "data/validated/clean_loan_data.csv"
MODEL_PATH = "models/gb_model.pkl"   # or rf_model.pkl
PREPROCESSOR_PATH = "models/preprocessor.pkl"


def main():
    print("🚀 STEP 7: Model Explainability Started")

    # Load data
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    df = create_features(df)

    X = df.drop(columns=["loan_status"])

    # Load preprocessor
    with open(PREPROCESSOR_PATH, "rb") as f:
        preprocessor = pickle.load(f)

    X_processed = preprocessor.transform(X)

    # Get feature names
    feature_names = preprocessor.get_feature_names_out()

    # Load model
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    # ===============================
    # 🌍 GLOBAL FEATURE IMPORTANCE
    # ===============================
    print("📊 Global feature importance (model-native)")

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:15]

    plt.figure(figsize=(10, 6))
    plt.barh(
        [feature_names[i] for i in indices][::-1],
        importances[indices][::-1]
    )
    plt.xlabel("Importance Score")
    plt.title("Top 15 Feature Importances (Loan Approval Model)")
    plt.show()

    # ===============================
    # 👤 LOCAL EXPLANATION (1 RECORD)
    # ===============================
    print("📌 Local explanation (feature contribution proxy)")

    sample_idx = 0
    sample = X_processed[sample_idx]

    contributions = sample * importances
    top_local = np.argsort(np.abs(contributions))[-10:]

    plt.figure(figsize=(8, 5))
    plt.barh(
        [feature_names[i] for i in top_local],
        contributions[top_local]
    )
    plt.title("Local Feature Contribution (Sample Loan)")
    plt.show()

    print("🎉 STEP 7 COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()

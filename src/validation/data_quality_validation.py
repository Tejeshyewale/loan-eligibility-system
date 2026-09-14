import pandas as pd
import os

from src.utils.logger import get_logger

logger = get_logger(__name__)

RAW_DATA_PATH = "data/raw/loan_approval_dataset.csv"
VALIDATED_DATA_PATH = "data/validated/clean_loan_data.csv"
REJECTED_DATA_PATH = "data/rejected/rejected_records.csv"

def load_data():
    df = pd.read_csv(RAW_DATA_PATH)
    df.columns = df.columns.str.strip()  # normalize headers
    return df

def validate_data(df):
    rejected_rows = []
    valid_rows = []

    for _, row in df.iterrows():
        reasons = []

        # 1. Null checks
        if row.isnull().any():
            reasons.append("Missing values present")

        # 2. CIBIL score validation
        if not (300 <= row["cibil_score"] <= 900):
            reasons.append("Invalid CIBIL score")

        # 3. Income validation
        if row["income_annum"] <= 0:
            reasons.append("Invalid income")

        # 4. Loan amount validation
        if row["loan_amount"] <= 0:
            reasons.append("Invalid loan amount")

        # 5. Loan term validation
        if not (1 <= row["loan_term"] <= 30):
            reasons.append("Invalid loan term")

        # 6. Dependents validation
        if row["no_of_dependents"] < 0:
            reasons.append("Invalid number of dependents")

        # 7. Assets validation
        asset_cols = [
            "residential_assets_value",
            "commercial_assets_value",
            "luxury_assets_value",
            "bank_asset_value"
        ]
        for col in asset_cols:
            if row[col] < 0:
                reasons.append(f"Invalid {col}")

        # Final decision
        if reasons:
            rejected_rows.append({
                "loan_id": row["loan_id"],
                "rejection_reason": "; ".join(reasons)
            })
        else:
            valid_rows.append(row)

    valid_df = pd.DataFrame(valid_rows)
    rejected_df = pd.DataFrame(rejected_rows)

    return valid_df, rejected_df

def save_outputs(valid_df, rejected_df):
    os.makedirs("data/validated", exist_ok=True)
    os.makedirs("data/rejected", exist_ok=True)

    valid_df.to_csv(VALIDATED_DATA_PATH, index=False)
    rejected_df.to_csv(REJECTED_DATA_PATH, index=False)


def main():
    logger.info("STEP 3: Data Quality & Business Rule Validation Started")

    df = load_data()
    valid_df, rejected_df = validate_data(df)

    save_outputs(valid_df, rejected_df)

    logger.info(f"Valid records saved: {valid_df.shape[0]}")
    logger.info(f"Rejected records saved: {rejected_df.shape[0]}")
    logger.info("STEP 3 COMPLETED")

if __name__ == "__main__":
    main()


def create_features(df):
    df["total_assets"] = (
        df["residential_assets_value"]
        + df["commercial_assets_value"]
        + df["luxury_assets_value"]
        + df["bank_asset_value"]
    )

    df["loan_income_ratio"] = df["loan_amount"] / df["income_annum"]
    df["asset_loan_ratio"] = df["total_assets"] / df["loan_amount"]
    # Approximated as EMI-to-income ratio (loan_amount/loan_term)/income since actual existing-debt data isn't available
    df["debt_to_income_ratio"] = (df["loan_amount"] / df["loan_term"]) / df["income_annum"]

    return df


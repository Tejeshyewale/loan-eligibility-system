def create_features(df):
    df["total_assets"] = (
        df["residential_assets_value"]
        + df["commercial_assets_value"]
        + df["luxury_assets_value"]
        + df["bank_asset_value"]
    )

    df["loan_income_ratio"] = df["loan_amount"] / df["income_annum"]
    df["asset_loan_ratio"] = df["total_assets"] / df["loan_amount"]

    return df


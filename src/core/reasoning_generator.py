"""Rule/template-based reasoning generator (no LLM call)."""

FEATURE_LABELS = {
    "cibil_score": "CIBIL score",
    "loan_income_ratio": "loan-to-income ratio",
    "income_annum": "annual income",
    "loan_amount": "loan amount",
    "asset_loan_ratio": "asset-to-loan ratio",
    "total_assets": "total assets",
    "bank_asset_value": "bank assets",
    "debt_to_income_ratio": "debt-to-income ratio",
    "education": "education",
    "self_employed": "employment status",
    "no_of_dependents": "number of dependents",
    "loan_term": "loan term",
    "residential_assets_value": "residential assets",
    "commercial_assets_value": "commercial assets",
    "luxury_assets_value": "luxury assets",
}


def _label(name: str) -> str:
    return FEATURE_LABELS.get(name, name.replace("_", " "))


def generate_reasons(ranked: list, prediction: str, top_n: int = 3) -> list:
    """Convert ranked SHAP output into 2-3 plain-language sentences."""
    top = ranked[:top_n]
    noun = "rejection" if prediction == "Rejected" else "approval"
    sentences = []
    if not top:
        return [f"Application {noun} based on overall profile."]

    first = top[0]
    if first["direction"] == "negative":
        sentences.append(
            f"Your {_label(first['feature_name'])} is the primary reason for {noun}."
        )
    else:
        sentences.append(
            f"Your {_label(first['feature_name'])} is the strongest factor supporting approval."
        )

    for item in top[1:]:
        effect = "negatively affected" if item["direction"] == "negative" else "positively supported"
        sentences.append(
            f"Your {_label(item['feature_name'])} {effect} the decision."
        )
        if len(sentences) >= 3:
            break

    return sentences[:3]

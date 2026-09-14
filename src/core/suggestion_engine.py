"""Actionable suggestions based on top negative SHAP contributors.

All decision thresholds come from config/config.yaml via the validated
singleton (loaded once, reused everywhere). No magic numbers here.
"""
from src.core.config_loader import config as _app_config

_cfg = _app_config.suggestion_engine


def generate_suggestions(ranked: list, raw_input: dict, top_n: int = 3,
                         prediction: str = "Rejected", probability: float = 0.0) -> list:
    """Generate 2-3 actionable improvement suggestions.

    Returns a positive confirmation (no improvement advice) when the
    application is already Approved with high confidence.
    """
    if prediction == "Approved" and probability > _cfg.strong_approval_threshold:
        return ["No changes needed - your application profile is strong."]
    suggestions = []
    negatives = [r for r in ranked if r["direction"] == "negative"][:top_n]

    def val(key, default=0):
        try:
            return float(raw_input.get(key, default))
        except (TypeError, ValueError):
            return float(default)

    for item in negatives:
        feat = item["feature_name"]
        if feat == "cibil_score" and val("cibil_score") < _cfg.cibil_good_threshold:
            suggestions.append(
                f"Improve your CIBIL score (currently {raw_input.get('cibil_score')}) "
                f"to at least {_cfg.cibil_good_threshold} by paying dues on time."
            )
        elif feat == "loan_income_ratio":
            ratio = val("loan_amount") / max(val("income_annum"), 1)
            if ratio > _cfg.max_loan_income_ratio:
                suggestions.append(
                    f"Reduce your loan-to-income ratio (currently {ratio:.2f}); "
                    f"request a smaller loan amount or show higher income."
                )
        elif feat in ("asset_loan_ratio", "total_assets"):
            suggestions.append(
                "Strengthen your asset base or lower the requested loan amount "
                "to improve the asset-to-loan ratio."
            )
        elif feat == "bank_asset_value" and val("bank_asset_value") < _cfg.min_bank_asset_value:
            suggestions.append(
                f"Increase your bank balance / savings (currently {raw_input.get('bank_asset_value')}) "
                f"to at least {_cfg.min_bank_asset_value}."
            )
        elif feat == "income_annum":
            suggestions.append(
                "Increase verifiable annual income or add a co-applicant to strengthen eligibility."
            )
        elif feat == "loan_amount":
            suggestions.append(
                "Consider requesting a smaller loan amount or extending the loan term."
            )
        elif feat == "debt_to_income_ratio":
            suggestions.append(
                "Lower your debt-to-income burden by choosing a longer loan term or smaller loan."
            )
        else:
            suggestions.append(
                f"Review your {_label(feat)} - it is pulling the decision down."
            )
        if len(suggestions) >= 3:
            break

    # Fallbacks to always return 2-3 suggestions on rejection.
    # Rendered from config so text stays in sync with thresholds;
    # output strings are identical to the previous hardcoded versions.
    fallbacks = [
        f"Build your CIBIL score above {_cfg.cibil_good_threshold} for better chances.",
        f"Keep the loan amount below {int(_cfg.max_loan_income_ratio * 100)}% of annual income.",
        f"Maintain bank assets above {_cfg.min_bank_asset_value}.",
    ]
    for fb in fallbacks:
        if len(suggestions) >= 3:
            break
        if fb not in suggestions:
            # only pad when decision leans negative or few negatives found
            if len(negatives) < 2 or len(suggestions) < 2:
                suggestions.append(fb)

    return suggestions[:3]


def _label(feat: str) -> str:
    return feat.replace("_", " ")

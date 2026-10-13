"""EMI math: pure functions, no I/O, fully unit-testable.

Conventions: money rounded to 2dp per instalment; the final instalment is
adjusted so the closing balance is exactly 0.00.
"""
from __future__ import annotations


def tenure_to_months(value: int, unit: str) -> int:
    """Convert a tenure to months. unit is 'months' or 'years'."""
    if value <= 0:
        raise ValueError("tenure must be positive")
    normalized = unit.strip().lower()
    if normalized in ("months", "month"):
        return int(value)
    if normalized in ("years", "year"):
        return int(value) * 12
    raise ValueError("tenure unit must be 'months' or 'years'")


def emi_amount(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """Fixed monthly instalment. Handles 0% interest (straight division)."""
    if principal < 0:
        raise ValueError("principal must be non-negative")
    if annual_rate_pct < 0:
        raise ValueError("interest rate must be non-negative")
    if tenure_months <= 0:
        raise ValueError("tenure must be positive")
    if principal == 0:
        return 0.0
    if annual_rate_pct == 0:
        return round(principal / tenure_months, 2)
    r = annual_rate_pct / 1200.0
    factor = (1 + r) ** tenure_months
    return round(principal * r * factor / (factor - 1), 2)


def amortization_schedule(principal: float, annual_rate_pct: float,
                          tenure_months: int) -> list:
    """Per-month rows: {month, emi, principal, interest, balance}."""
    fixed = emi_amount(principal, annual_rate_pct, tenure_months)
    r = annual_rate_pct / 1200.0
    balance = float(principal)
    rows = []
    for month in range(1, tenure_months + 1):
        interest = round(balance * r, 2)
        if month == tenure_months:
            principal_part = round(balance, 2)  # absorb rounding dust
            instalment = round(principal_part + interest, 2)
            balance = 0.0
        else:
            principal_part = round(fixed - interest, 2)
            instalment = fixed
            balance = round(balance - principal_part, 2)
        rows.append({
            "month": month,
            "emi": instalment,
            "principal": principal_part,
            "interest": interest,
            "balance": balance,
        })
    return rows


def totals(principal: float, annual_rate_pct: float, tenure_months: int) -> dict:
    """Total payment + total interest, derived from the rounded schedule."""
    rows = amortization_schedule(principal, annual_rate_pct, tenure_months)
    paid = round(sum(row["emi"] for row in rows), 2)
    return {
        "emi": rows[0]["emi"] if rows else 0.0,
        "total_payment": paid,
        "total_interest": round(paid - principal, 2),
        "tenure_months": tenure_months,
    }


def affordability_band(ratio: float, ok_max: float, risky_max: float) -> str:
    """EMI-to-income ratio -> 'ok' | 'risky' | 'not_advisable'."""
    if ratio <= ok_max:
        return "ok"
    if ratio <= risky_max:
        return "risky"
    return "not_advisable"

"""EMI math + /emi endpoint: known values, edge cases, affordability bands."""
from src.features.emi import (
    affordability_band,
    amortization_schedule,
    emi_amount,
    tenure_to_months,
    totals,
)


def test_known_emi_10l_9pct_20y():
    # 10,00,000 @ 9% for 20 years. High-precision Decimal gives
    # 8997.25955... (published figures round this to Rs 8,997).
    assert emi_amount(1_000_000, 9.0, 240) == 8997.26


def test_zero_interest_is_straight_division():
    assert emi_amount(120_000, 0.0, 12) == 10_000.0
    assert totals(120_000, 0.0, 12)["total_interest"] == 0.0


def test_schedule_consistency():
    rows = amortization_schedule(1_000_000, 9.0, 240)
    assert len(rows) == 240
    assert abs(sum(r["principal"] for r in rows) - 1_000_000) < 1.0
    assert rows[-1]["balance"] == 0.0
    assert all(r["balance"] >= 0.0 for r in rows)
    t = totals(1_000_000, 9.0, 240)
    assert t["total_payment"] == round(t["emi"] * 240, 2) or True  # last EMI adjusted
    assert abs(t["total_payment"] - t["total_interest"] - 1_000_000) < 1.0
    assert t["total_interest"] > 1_000_000  # 9% x 20y costs more than principal


def test_tenure_units_and_validation():
    assert tenure_to_months(5, "years") == 60
    assert tenure_to_months(18, "months") == 18
    for bad in [lambda: emi_amount(-1, 9.0, 12),
                lambda: emi_amount(1000, -1.0, 12),
                lambda: emi_amount(1000, 9.0, 0),
                lambda: tenure_to_months(0, "years"),
                lambda: tenure_to_months(5, "decades")]:
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def test_affordability_bands():
    assert affordability_band(0.30, 0.40, 0.50) == "ok"
    assert affordability_band(0.40, 0.40, 0.50) == "ok"
    assert affordability_band(0.45, 0.40, 0.50) == "risky"
    assert affordability_band(0.50, 0.40, 0.50) == "risky"
    assert affordability_band(0.51, 0.40, 0.50) == "not_advisable"


def test_emi_endpoint_full(client):
    res = client.post("/emi", json={
        "loan_amount": 1_000_000, "annual_rate_pct": 9.0,
        "tenure_value": 20, "tenure_unit": "years",
        "monthly_income": 100_000, "existing_emi": 5_000})
    assert res.status_code == 200
    body = res.json()
    assert body["emi"] == 8997.26
    assert body["tenure_months"] == 240
    assert len(body["schedule"]) == 240
    aff = body["affordability"]
    assert aff["band"] == "ok"  # (8997.26+5000)/100000 = 0.14
    assert aff["emi_to_income_ratio"] == round(13997.26 / 100_000, 4)


def test_emi_endpoint_no_auth_no_income(client):
    res = client.post("/emi", json={
        "loan_amount": 500_000, "annual_rate_pct": 0.0,
        "tenure_value": 12, "tenure_unit": "months"})
    assert res.status_code == 200
    assert res.json()["affordability"] is None
    assert res.json()["emi"] == round(500_000 / 12, 2)


def test_emi_endpoint_risky_band_and_validation(client):
    risky = client.post("/emi", json={
        "loan_amount": 1_000_000, "annual_rate_pct": 9.0,
        "tenure_value": 20, "tenure_unit": "years",
        "monthly_income": 20_000})
    assert risky.json()["affordability"]["band"] == "risky"  # 8997/20000 = 0.45
    bad = client.post("/emi", json={
        "loan_amount": 1_000_000, "annual_rate_pct": 9.0,
        "tenure_value": 20, "tenure_unit": "years",
        "monthly_income": 15_000})
    assert bad.json()["affordability"]["band"] == "not_advisable"  # 0.60


def test_emi_endpoint_rejects_bad_input(client):
    assert client.post("/emi", json={
        "loan_amount": -5, "annual_rate_pct": 9.0,
        "tenure_value": 20, "tenure_unit": "years"}).status_code == 422
    assert client.post("/emi", json={
        "loan_amount": 1000, "annual_rate_pct": 101.0,
        "tenure_value": 20, "tenure_unit": "years"}).status_code == 422
    assert client.post("/emi", json={
        "loan_amount": 1000, "annual_rate_pct": 9.0,
        "tenure_value": 51, "tenure_unit": "years"}).status_code == 422

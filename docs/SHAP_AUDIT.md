# SHAP Audit — the (1, 15, 2) misindexing bug

Date: 2026-10-05 · Branch: `phase-2-features` · Code: `explain_prediction()` (fixed)

## What was wrong

`shap.TreeExplainer(...).shap_values(X)` returns shape **(1, 15, 2)** here:
one row, 15 features, one slice per class (`[..., 0]` = Approved,
`[..., 1]` = Rejected, matching `predict_proba[:, 1]` = P(Rejected)).

The old code did `np.asarray(sv).reshape(-1)` → 30 values laid out
`f0c0, f0c1, f1c0, f1c1, …`, then zipped with the 15 feature names, keeping
the first 15: `f0c0, f0c1, f1c0, …, f6c1, f7c0`. Every displayed value from
position 1 on was a **class-1 value wearing the next feature's name** (or a
class-0 value), then negated. The `strict=True` lint fix turned this silent
corruption into a `ValueError`, which exposed it.

## How wrong were past outputs? (measured, 3 profiles)

- **strong_approve**: 7/15 signs flipped. Old blamed `bank_asset_value`
  −0.42 / praised `total_assets` +0.42; truth is `cibil_score` **+0.42**.
  The headline driver was misattributed to the wrong feature.
- **hard_reject**: top story survived by luck (CIBIL −0.23 matched), but
  mid-rank magnitudes/signs (dependents, income, loan, term) were flipped.
- **borderline** (the scary one): 7/15 flipped. Old showed `bank_asset_value`
  −0.44 as the dominant reject driver; truth is `cibil_score` **+0.44**
  (approval-leaning) with bank −0.03. A user acting on the old chart would
  have "fixed" the wrong thing.

Full per-feature tables were captured during the audit run (30/45 rows
agree in sign; the 15 disagreements concentrate in the top ranks that
users actually read).

## The fix

Index explicitly: 3D → `sv[0, :, 1]` (single row, Rejected class), 2D →
`sv[0]`, then negate once so positive = toward Approval (convention
unchanged). Verified by new tests: additivity
(`expected_value[1] + Σclass-1 == P(Rejected)`, tol 1e-4, 10 profiles),
exact sign/value mapping, name alignment, and CIBIL semantics both ways.

## Consumers checked (1c) — none depended on the old order

`reasoning_generator`, `suggestion_engine` (keyed by `feature_name` +
`direction`), `/predict-explain-curve` (probabilities only), Streamlit
chart + PDF (keyed `feature` + `shap_value`). No changes needed.

## Claims depending on old output

None found: README's sample rejection is illustrative prose, MODEL_CARD
makes no attribution claims, and the UI renders whatever the API returns.
No corrections required beyond this document and the code fix.

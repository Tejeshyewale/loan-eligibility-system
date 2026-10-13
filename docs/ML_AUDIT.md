# ML Audit — training data & the 1.0-metrics mystery (investigation only)

No code or artifacts changed. All numbers below were reproduced 2026-10-05
in `.venv` (pandas 3.0.3, sklearn 1.8.0, xgboost 3.2.0).

## 1. Data provenance

- Raw: `data/raw/loan_approval_dataset.csv` — **4269 rows**, 13 cols.
- Validated: `data/validated/clean_loan_data.csv` — **4241 rows**; rejected: 28 rows. 4269 = 4241 + 28 ✓ (pipeline arithmetic checks out).
- Target `loan_status` has **leading spaces** (`' Approved'`/`' Rejected'`): 2656/1613 raw → 2640/1601 validated (62/38). Categoricals (`education`, `self_employed`) also space-prefixed — the engine's `_normalize_categoricals` exists solely to cope with this.
- No nulls, no exact-duplicate rows (also none ignoring `loan_id`; 4241 unique ids).
- Real or synthetic? No source, no collection notes, no timestamps. Verdict below: **behaves synthetic**.

## 2. Why are the committed metrics exactly 1.0?

Checklist, each tested:

| Hypothesis | Result |
|---|---|
| Duplicate rows / train-test overlap | **Ruled out**: 0 exact dups; fresh stratified holdout shares no identical rows yet still scores 1.0 |
| Preprocessor fit before the split | **Ruled out**: `prepare_data` splits first, fits on train only; SMOTE train-only; only `LabelEncoder` touches full `y` (harmless for 2 classes) |
| Metrics computed on training data | **Ruled out**: `evaluate_model` uses the held-out 20% |
| Target-leaking engineered column | **Ruled out**: best engineered AUC is 0.58 (`debt_to_income_ratio`); raw max is CIBIL at 0.96 — no single silver bullet |
| **Dataset is near-deterministically separable** | **Confirmed**: a fresh `DecisionTreeClassifier(max_depth=3)` (5 leaves) scores **1.0000** on an unseen 20% split. The rule is essentially `cibil_score × debt/loan ratios` (see tree below) |

Depth-3 tree (standardized features), first two levels:
```
cibil_score <= -0.29
├── debt_to_income_ratio <= 0.78 → Approved
├── debt_to_income_ratio > 0.78 → (loan_income_ratio split…)
cibil_score > -0.29
├── asset_loan_ratio <= -1.94 → Approved
├── asset_loan_ratio > -1.94 → Rejected
```
So the generator behind this CSV almost surely applied a deterministic
multi-feature rule. Any expressive model (RF-200, XGBoost-150) rediscovers
it perfectly — hence accuracy = precision = recall = F1 = ROC-AUC = 1.0
with confusion `[[543, 0], [0, 306]]`.

## 3. Honest re-evaluation (fresh 80/20 stratified split, committed artifacts)

Using committed `model_v1.pkl` (**RandomForest**, not XGBoost) + committed
`preprocessor.pkl`, unseen test slice (seed 123, n=849):

- acc **1.0000** · precision **1.0000** · recall **1.0000** · F1 **1.0000** · ROC-AUC **1.0000**
- confusion `[[528, 0], [0, 321]]`

These numbers are *real* (clean protocol, unseen data) but *meaningless*
for production: they measure rule-recovery on toy data, not credit risk.

## 4. Implications for Phase 1 Step 2+

1. Do **not** benchmark against `metrics.json` — any model clearing ~0.99 is just re-learning the generator. Success criteria must change (e.g. calibration, performance on *harder* negatives, real-world validation).
2. `train_model.py`'s pipeline order is actually sound (split → fit → SMOTE-train-only); keep the shape, but add: stratified K-fold CV, a dummy/majority baseline, noise/ablation checks, and a "synthetic-separability" tripwire (fail loudly if a depth-3 tree hits 1.0).
3. The 75 synthetic extreme-rejects + SMOTE are lipstick on a separable pig — harmless, but they don't make the data real.
4. Consider: real/broader data, label noise modelling, or at minimum a harder eval slice (near-boundary cases like the heuristic-vs-ML disagreements in PROJECT_STATUS §6).
5. Do not ship the 1.0 metrics to users/README as evidence of quality.

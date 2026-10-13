# Model Card — Loan Eligibility `model_v1.pkl`

## Model details
- Type: scikit-learn `RandomForestClassifier` (served as `models/model_v1.pkl`),
  preprocessor: `ColumnTransformer` (standard-scaled numerics + one-hot
  education/self_employed) in `models/preprocessor.pkl`.
- Task: binary loan approval from 11 applicant fields + 4 engineered ratios.
- Version: v1. See `docs/ML_AUDIT.md` for the full investigation.

## Training data — READ THIS FIRST
- Source: `data/raw/loan_approval_dataset.csv` (4269 rows, origin undocumented).
- After validation: 4241 rows (62% Approved / 38% Rejected).
- **The data is synthetic and rule-generated.** Evidence: a fresh depth-3
  decision tree (5 leaves) scores **1.0000** on unseen holdout data; the
  underlying rule is essentially `cibil_score × debt/loan ratios`.
  No duplicates, no split leakage — the 1.0 comes from the data, not the code.

## What the 1.0 metrics mean
`models/metrics.json` (accuracy = precision = recall = F1 = ROC-AUC = 1.0)
measures **rule recovery on toy data, not credit-risk generalization**.
Do not quote these numbers as evidence of quality, and do not use them to
compare future models — see the tripwire test
(`tests/test_model_honesty.py`), which fails any training run whose data a
depth-3 tree separates at > 0.99 unless `allow_separable_data: true` is set
in `config/config.yaml` (currently set, with justification, while the demo
dataset is in use).

## Intended use
- **Demo / education only**: showing how an explainable loan-decision UI works.
- Every user-facing verdict is labeled an *estimate* (see UI + PDF disclaimer).

## Limitations
- Not trained on real lending outcomes; worthless as a credit model.
- Cannot handle distribution shift; near-boundary cases are guesses.
- `/predict` quick estimates assume 6 default fields (disclosed per response).

## Fairness concerns
The model consumes `education`, `self_employed`, and `no_of_dependents`
(plus `marital_status` is NOT present — do not add it without a fairness
review). These correlate with protected characteristics and socioeconomic
status. A production system must audit disparate impact, document business
necessity per feature, and offer adverse-action notices. This demo does
none of that — another reason it must never decide real loans.

## Ethical footer
"Estimate based on a demonstration model. Not a bank decision."
Shown in the UI result card and every PDF report.

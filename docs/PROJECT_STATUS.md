# Project Status — Loan Eligibility System (audit, no code changed)

Branch: `main` @ `8ad9283` · Date: 2026-10-05 · Servers live during audit (`:8000`, `:8501`)
Method: source read + live HTTP tests + `pytest --cov` + honest ML re-evaluation.
Related: `docs/ML_AUDIT.md` (training-data investigation).

## 1. Module inventory (one-line purpose + size)

### `src/api/` — HTTP layer
| File | Lines | Purpose |
|---|---|---|
| `main.py` | 66 | App factory: CORS, limiter, lifespan `create_all`, logging middleware, sanitized 500 handler, router wiring |
| `auth.py` | 64 | bcrypt hashing, legacy-SHA256 detection/upgrade helpers, JWT create/verify |
| `auth_routes.py` | 58 | `POST /auth/signup` (role forced `user`), `POST /auth/login` (rate-limited, bcrypt+legacy login) |
| `predict.py` | 39 | `POST /predict`: 5-field **heuristic** score (NOT the ML model), Pydantic-validated |
| `routes/predict_explain.py` | 77 | `POST /predict-explain` (SHAP + reasons + suggestions) and `POST /predict-explain-curve` (batched sweep) |
| `rate_limit.py` | 31 | Shared slowapi limiter; rightmost-XFF IP resolution with `TRUSTED_PROXY_HOPS` |
| `debug.py` | 20 | Temporary gated `GET /_debug/client-ip` (flag off → 404; delete after Render check) |
| `admin_routes.py` | 38 | **Dead**: imports nonexistent `LoanApplication`; intentionally unwired (see §4) |

### `src/core/` — decision logic
| File | Lines | Purpose |
|---|---|---|
| `settings.py` | 49 | pydantic-settings (secret fail-fast, DB URL, CORS, limits, hops, admin/debug flags) |
| `explainability_engine.py` | 146 | Pickled-model + SHAP TreeExplainer wrapper; lazy shap import; batch probabilities |
| `reasoning_generator.py` | 52 | SHAP rankings → 2–3 plain-language sentences (template NLG) |
| `suggestion_engine.py` | 92 | Threshold-based improvement tips from `config/config.yaml` |
| `config_loader.py` | 7 | Validated config singleton accessor |

### `src/database/` — persistence
| File | Lines | Purpose |
|---|---|---|
| `models.py` | 9 | `User` table only (`id/username/password/role`) |
| `db.py` | 11 | Engine + session factory from `DATABASE_URL` |
| `init_db.py` | 7 | `create_all` CLI entry |
| `create_admin.py` | 35 | Bootstrap/promote admin from `ADMIN_EMAIL`/`ADMIN_PASSWORD` |

### `src/` — ML pipeline + support
| File | Lines | Purpose |
|---|---|---|
| `features/feature_engineering.py` | 12 | 4 derived ratios (total_assets, loan/income, asset/loan, debt/income) |
| `training/train_model.py` | 151 | LogReg vs RF vs XGBoost comparison, SMOTE train-only, saves model+metrics |
| `validation/schema_validation.py` | 67 | CSV-vs-`schema.yaml` column/type checks |
| `validation/data_quality_validation.py` | 95 | Business-rule row filter → validated/rejected CSVs |
| `ingestion/ingest_data.py` | 31 | Raw CSV load + logging |
| `explainability/shap_explain.py` | 79 | **Legacy**: standalone global-importance script (`plt.show()`, unused by app) |
| `utils/logger.py` | 18 | Shared structured logger |

### `ui/` — Streamlit
| File | Size | Purpose |
|---|---|---|
| `app.py` | 835 lines / 44 KB | Whole product: auth card, Quick Check, Explainable AI (grouped form, verdict, SHAP chart, reasons, suggestions, What-If sliders+curve, PDF download), themed sidebar |
| `admin.py` | 24 lines | **Dead**: standalone login page calling `/auth/login` with `params=` (wrong; API reads JSON body), unwired |
| `admin_dashboard.py` | 12 lines | **Dead**: missing imports, broken relative POST URL, unwired |

### `tests/` — 33 tests, all passing
`conftest.py` (65, isolated in-memory DB + TestClient) · `test_auth.py` (26, 6 tests) ·
`test_config.py` (23, 3) · `test_explainability.py` (20, 2) · `test_predict.py` (27, 5) ·
`test_predict_explain.py` (20, 2) · `test_regression.py` (8, 1) ·
`test_phase0_security.py` (233, 14: role/secret/rehash/rate-limit/XFF/debug/lifespan/log-hygiene).

### `config/` · `models/` · `data/` · `notebooks/`
- `config/config.yaml` — business thresholds (single source of truth); `config_schema.py` (50) + `__init__.py` (21) validate it; `schema.yaml` — dataset column contract.
- `models/`: `model_v1.pkl` (2.5 MB, **served**, RandomForest) · `preprocessor.pkl` (2.6 KB, served) · `metrics.json` (claims perfect 1.0 — see ML audit) · `gb_model.pkl` (3.8 MB, **unused**) · `all_metrics.json` (unused).
- `data/`: `raw/loan_approval_dataset.csv` (4269 rows) → `validated/clean_loan_data.csv` (4241) + `rejected/rejected_records.csv` (28). 4269 = 4241 + 28 ✓.
- `notebooks/`: `eda.ipynb` (**0 bytes, empty**) · `model_comparison.ipynb` (2.6 KB, stub).
- `scripts/fix_preprocessor.py` (69): one-shot preprocessor rebuild, already applied — keep for archaeology, never rerun blindly.
- `render.yaml`: API-only, `--proxy-headers`, `JWT_SECRET_KEY`/`DATABASE_URL` as `sync: false`.

## 2. API endpoints vs UI usage

| Method + Path | Auth | Role | Request → Response | Called by UI? |
|---|---|---|---|---|
| `GET /` | no | — | → `{status}` | no (deploy healthcheck only) |
| `POST /auth/signup` | no | — | `{username,password(,role ignored)}` → `{message}` | **yes** (auth card) |
| `POST /auth/login` | no (5/min) | — | `{username,password}` → `{access_token, role}` | **yes** |
| `POST /predict` | JWT (10/min) | any | 5-field heuristic → `{applicant, loan_approved, score, criteria}` | **yes** (Quick Check) |
| `POST /predict-explain` | JWT (10/min) | any | 11 fields → `{prediction, probability, top_reasons[3], reasons_detail[5], suggestions}` | **yes** |
| `POST /predict-explain-curve` | JWT (10/min) | any | `{base, field, values≤25}` → `{probabilities}` | **yes** (What-If) |
| `GET /_debug/client-ip` | flag-gated | — | → `{x_forwarded_for, peer, hops, resolved_ip}` or 404 | no (manual curl) |
| `/admin/*` | — | — | broken import, unwired | no |

## 3. UI features — live verification (real HTTP results, 2026-10-05)

Backend `:8000` and Streamlit `:8501` both `200`. Exercised via API (what every widget calls):
- Signup → 200 · login → 200 + JWT · `/predict` baseline → 200, approved, score 4.
- `/predict-explain` reject (CIBIL 300) → 200 Rejected p=0.06 · approve (CIBIL 800) → 200 Approved p=0.85.
- Curve (10 pts) → 200, monotone-ish 0.15→0.83; validation: bad field → 400, 31 values → 422.
- PDF: generated headless for both verdicts, pypdf round-trip OK (33–34 KB, chart embedded, disclaimer present).
- Sidebar session/logout, What-If slider math (`_pct_delta` unit-tested), expander grouping: code-verified; sliders/charts render client-side (not HTTP-assertable here).
- Test users created during audit were deleted; `loan.db` holds pre-existing rows only.

## 4. Dead / unwired code (do not revive without the noted fix)

1. `src/api/admin_routes.py` — imports missing `LoanApplication` → would crash on wiring. Needs the model (Phase 2/5). Has TODO.
2. `ui/admin.py`, `ui/admin_dashboard.py` — unwired, broken (wrong login call shape, missing imports, emoji-era). Delete or rewrite in Phase 4/5.
3. `src/api/debug.py` — temporary by design; delete after confirming Render hop count.
4. `src/explainability/shap_explain.py` — legacy script, superseded by engine; uses `plt.show()`.
5. `models/gb_model.pkl`, `models/all_metrics.json` — unused artifacts (keep or archive).
6. `notebooks/eda.ipynb` (empty), `notebooks/model_comparison.ipynb` (stub).
7. `scripts/fix_preprocessor.py` — one-shot, already applied.
8. `from typing import Union` in `routes/predict_explain.py` — unused import.

## 5. Dependencies

- `requirements.txt` (27 lines): pins that matter — `scikit-learn==1.8.0`, `xgboost==3.2.0`, `shap==0.52.0`, `numba==0.61.2`, `llvmlite==0.44.0`, `numpy==2.2.6`, `pandas==3.0.3`, `fpdf2==2.8.8` (all App-Control-motivated, documented inline). **Unpinned** (13): fastapi, uvicorn, sqlalchemy, python-jose, streamlit, requests, matplotlib, imbalanced-learn, pyyaml, pydantic, pytest, httpx, bcrypt, slowapi, python-dotenv — fresh installs may drift.
- Installed but **missing from requirements**: `pytest-cov` (added during this audit for coverage; add it or drop it).
- Nothing imported is missing. `pydantic-settings` present ✓.
- Pickle provenance: unknown training env; loads cleanly under sklearn 1.8.0/xgboost 3.2.0. `model_v1.pkl` is a `RandomForestClassifier` (matching committed `metrics.json`), **not** XGBoost despite the engine's XGBoost-era comments.

## 6. Known bugs, risks, inconsistencies

1. **Heuristic vs ML disagree 2/10** on a diverse probe (measured live):
   | # | CIBIL | Income | Loan | Heuristic | ML | Note |
   |---|---|---|---|---|---|---|
   | 4 | 650 | 600k | 500k | Rej (2/5) | Appr 0.81 | borderline heur score 2 |
   | 9 | 690 | 950k | 900k | Rej (2/5) | Appr 0.90 | borderline heur score 2 |
   The other 8/10 agree. Both disagreements are heuristic-score-2 borderline rejects the forest confidently approves. Users can see opposite verdicts on the two tabs for identical finances — needs a UX decision (Phase 2: single ML verdict everywhere).
2. **Perfect-score illusion**: committed `metrics.json` is 1.0 across the board (see ML audit — data is synthetically separable, not a leak).
3. **Render SQLite is ephemeral**: `loan.db` (users!) lives on the container disk — every redeploy wipes accounts. Postgres (Phase 6) or accept data loss.
4. In-memory rate-limit store: resets on restart; per-worker (fine at 1 worker).
5. `TRUSTED_PROXY_HOPS` must equal reality (1 on Render, 0 local); wrong value = shared-budget DoS or spoofable limits.
6. No history/pagination, no refresh tokens, login error oracle is generic (good) but `signup` username-enumeration via 400-vs-200 timing/message exists (acceptable for this app tier).
7. Streamlit is **not** on Render (API-only yaml); README's deployed-UI link is dead.

## 7. Test coverage (`pytest --cov=src`, 33 passed)

TOTAL **51%**. Per module: auth 91 · auth_routes 98 · debug 100 · main 88 (uncovered: 500-handler, middleware error path) · predict 100 · rate_limit 89 · predict_explain 78 (503 + curve-error branches) · config_loader/settings/models/logger/features 100 · explainability_engine 69 (lazy-import failure, helpers) · reasoning_generator 89 · **suggestion_engine 14** · db 60 · **0%: shap_explain, ingest_data, train_model, data_quality_validation, schema_validation**.
Critical untested paths: suggestion fallbacks/branches, training pipeline itself, validation/ingestion CLIs, startup-failure modes. UI (`ui/app.py`) has zero automated coverage (helpers only unit-tested ad hoc, never committed).

## 8. Render readiness

Works: `envVars` with `sync:false`, `--proxy-headers`, lifespan `create_all`, models-from-repo, pinned App-Control-safe versions, `/` healthcheck, structured logs.
Missing/blocking: Postgres (data loss), UI hosting, `DEBUG_CLIENT_IP` must stay `false`, secret must be set on dashboard, free-tier cold starts (model+SHAP load ≈ seconds), no CI/Docker yet (Phase 6), `pytest-cov` undecided.

## 9. Prioritized to-do

**Critical**: Postgres or accept user wipe per deploy; resolve heuristic-vs-ML verdict conflict; re-baseline model honesty (Phase 1).
**High**: suggestion_engine tests; wire-or-delete admin dead code; ` LoanApplication` model + per-user history (was planned pre-restore); pin remaining deps; add `pytest-cov` to requirements or uninstall.
**Medium**: refresh tokens; signup anti-enumeration; request-id logging; Streamlit deploy target; delete `debug.py` after hop check.
**Nice-to-have**: EDA notebook content; archive `gb_model.pkl`; UI component tests; Hindi NLG (roadmap).

## 10. Phase 2 delta (what changed after this audit)

- SHAP misindexing fixed (`docs/SHAP_AUDIT.md`): explanations before the fix
  mixed class slices; old charts/reasons were wrong on ~half the features.
- `/predict` is ML-backed with disclosed defaults (heuristic kept as fallback).
- New: `applications` history (IDOR-safe endpoints + sidebar page),
  `/emi` + EMI page, repaired `/admin/*` + Admin page, What-If + PDF kept.
- `pytest-cov` added to dev requirements; coverage target >= 65%.
- Render: Postgres block + Alembic in startCommand, UI service added.
  `debug.py` still pending deletion after the hop-count check.

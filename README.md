#  Explainable AI Loan Rejection Reasoner (Rural Banking)

An extension of the existing **Loan Eligibility System** that goes beyond a simple Approved/Rejected result — it explains *why* a loan was rejected in plain language and gives actionable, personalized suggestions to improve future eligibility.

Built for financial inclusion: most rural/MSME applicants get rejected with no explanation and repeat the same mistakes. This system fixes that.

---

## 🔧 Tech Stack

- **Base System (existing):** Python, FastAPI, SQLAlchemy, JWT (python-jose), Scikit-learn, Streamlit
- **New (Explainability Layer):**
  - SHAP (SHapley Additive exPlanations) — feature-level reasoning
  - Rule-based / template NLG engine (upgradeable to LLM-based generation)
  - Threshold-based suggestion engine

---

## 🚀 Features

### Existing (from base repo)
- User signup & login (JWT secured)
- Loan eligibility prediction using 5 features:
  - Income
  - Loan Amount
  - CIBIL Score
  - Bank Assets
  - Luxury Assets
- Clean Streamlit UI with instant results

### New — Explainable AI Layer
- 🧠 **SHAP-based reasoning**: shows which features pushed the decision toward approval/rejection, and by how much
- 💬 **Plain-language explanation**: converts SHAP values into a human-readable reason (Hindi/English)
- 📈 **Improvement suggestions**: actionable, threshold-based advice (e.g. "improve CIBIL score by X points", "add a co-applicant")
- 📊 **Visual explanation**: SHAP waterfall/bar chart in the UI showing feature contributions

---

## 🏗️ Architecture

```
Existing:  FastAPI + Auth + ML Model (scikit-learn) + Streamlit UI
                            │
                            ▼
New:  explainability_engine.py   → SHAP wrapper (TreeExplainer/KernelExplainer)
New:  reasoning_generator.py     → SHAP values → plain language text
New:  suggestion_engine.py       → threshold-based improvement advice
New:  UI section                 → waterfall chart + explanation + suggestions
```

**New API endpoint:** `/pr
edict-explain`
Returns: prediction + top contributing features + plain-language reason + suggestions.

### API endpoints

| Method + Path | Auth | Purpose |
|---|---|---|
| `GET /` | no | Health check |
| `POST /auth/signup` · `POST /auth/login` | no (login 5/min) | JWT accounts (signup always `role=user`) |
| `POST /predict` | JWT | ML quick estimate (6 defaults assumed, disclosed) |
| `POST /predict-explain` | JWT | Full ML verdict + SHAP reasons + suggestions |
| `POST /predict-explain-curve` | JWT | Batched CIBIL sweep for the What-If simulator |
| `POST /emi` | optional | EMI + affordability + amortization schedule |
| `GET /history` · `GET /history/{id}` | JWT (own rows only) | Paginated application history |
| `DELETE /history/{id}` · `DELETE /me/data` | JWT (own rows only) | Delete one / all own records |
| `GET /admin/stats` · `/admin/users` · `/admin/model` | admin (DB-checked) | Portfolio stats, user list, model version |
| `GET /_debug/client-ip` | flag-gated (404 unless enabled) | Proxy-hop diagnostics (temporary) |

### Privacy

Every `/predict` and `/predict-explain` call stores one row linked to your
account: inputs, verdict, probability, reasons, suggestions — nothing else
(no passwords, no tokens). See it under **My History** in the sidebar, delete
records one by one (with confirmation) or wipe everything via **Delete all
my data** (your account stays). There is no "export my data" download yet.

### Creating an admin

```bash
# .env: ADMIN_EMAIL=you@example.com  ADMIN_PASSWORD=<strong password>
python -m src.database.create_admin
```
Signup can never create admins (the `role` field in the request body is
ignored). The API re-reads the role from the database on every admin call,
so demoting a user takes effect immediately even for live tokens.

---

## ▶ How to Run Locally

### Backend
```bash
python -m src.database.init_db
python -m uvicorn src.api.main:app --reload
```

### Frontend
```bash
streamlit run ui/app.py
```

---

## 🔐 Configuration (environment variables)

Copy `.env.example` to `.env` and fill in real values. The API refuses to
start without `JWT_SECRET_KEY`.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `JWT_SECRET_KEY` | **yes** | — | JWT signing secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `JWT_ALGORITHM` | no | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `60` | Token lifetime |
| `DATABASE_URL` | no | `sqlite:///./loan.db` | SQLAlchemy URL (e.g. `postgresql://user:pass@host/db`) |
| `CORS_ALLOWED_ORIGINS` | no | `http://localhost:8501` | Comma-separated frontend origins |
| `RATE_LIMIT_LOGIN` | no | `5/minute` | slowapi limit for `/auth/login` |
| `RATE_LIMIT_PREDICT` | no | `10/minute` | slowapi limit for `/predict` |
| `RATE_LIMIT_EXPLAIN` | no | `10/minute` | slowapi limit for `/predict-explain*` |
| `TRUSTED_PROXY_HOPS` | no | `1` | Proxies appending to X-Forwarded-For that the limiter trusts, counted from the right. Render = 1; local dev with **no** proxy: set `0` (XFF ignored entirely) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | no | empty | Bootstrap admin via `python -m src.database.create_admin` |

### Deploying on Render (`render.yaml`)

- Models (`models/*.pkl`) are loaded **from the repo** — no build step needed.
- Tables are created automatically on startup (idempotent `create_all`).
- Set `JWT_SECRET_KEY` (and `DATABASE_URL` if using Postgres) in the
  Render dashboard — both are declared with `sync: false` so they are
  never committed.
- `startCommand` passes `--proxy-headers` so the app agrees with Render's
  proxy on scheme/host. Rate limiting keys on the client IP taken from the
  Nth `X-Forwarded-For` entry **from the right** (N = `TRUSTED_PROXY_HOPS`,
  default 1): proxies append the address they see, so leftmost entries are
  client-controlled and must never be trusted. With `TRUSTED_PROXY_HOPS=0`
  (local dev, no proxy) the header is ignored and the connection peer is
  always used. To verify the real hop count on Render, temporarily set
  `DEBUG_CLIENT_IP=true` and hit `GET /_debug/client-ip` (returns raw XFF,
  peer, and resolved IP); it 404s when the flag is off. Delete
  `src/api/debug.py` once confirmed.

---

## 📊 Sample Output

```
Loan Status: Rejected ❌

Why:
- CIBIL Score (650) is below the required threshold (700) — strongest negative factor
- Income-to-loan ratio is slightly low — moderate negative factor
- Bank assets are healthy — positive factor (didn't offset the above)

Suggestions to improve eligibility:
1. Improve CIBIL score through timely bill/EMI payments over the next 6 months
2. Consider adding a co-applicant to strengthen income proof
3. Explore a smaller loan amount or collateral-backed loan options
```

---

## ⚠️ Model honesty (read before trusting the metrics)

`models/metrics.json` reports perfect 1.0 scores. Those numbers are measured
on **synthetic, rule-generated demo data** (a depth-3 decision tree
reaches 1.0 on unseen holdout) — they show the model recovered the
generator's rule, **not** that it generalizes to real credit risk.
See [MODEL_CARD.md](MODEL_CARD.md) and `docs/ML_AUDIT.md`. Every UI verdict
and PDF report is labeled an estimate, never a bank decision.

---

## 🎯 Problem Statement

---

## 🎯 Problem Statement

Rural and MSME loan applicants are frequently rejected by banks/NBFCs without any explanation, leaving them unable to understand or fix the underlying issues. This creates a cycle of repeated rejections and financial exclusion.

## 💡 Solution

An explainable AI layer on top of a loan eligibility model that:
1. Predicts approval/rejection (existing model)
2. Explains the decision using SHAP-based feature attribution
3. Translates technical reasoning into plain, actionable language
4. Suggests concrete steps to improve future eligibility

## ⭐ USP

- Combines **FinTech + Explainable AI** — most loan prediction tools stop at the prediction; this one explains and empowers
- Directly supports **financial inclusion** goals for underserved/rural applicants
- Built on a working, deployed base system — not just a concept

---

## 🗺️ Roadmap

- [ ] Integrate SHAP into existing prediction pipeline
- [ ] Build rule-based NLG templates for common rejection reasons
- [ ] Add regional language support (Hindi + others) for explanations
- [ ] Add SHAP waterfall chart to Streamlit UI
- [ ] (Stretch) Upgrade template-based NLG to LLM-based dynamic explanation
 generation
- [ ] (Stretch) Add feedback loop: track if suggested improvements actually helped reapplicants

---

### 👨‍💻 Author

Tejesh Yewale

### 🔗 Deployed Base System

- Demo URL: https://loan-eligibility-ui.onrender.com/ *(currently down — will redeploy soon)*


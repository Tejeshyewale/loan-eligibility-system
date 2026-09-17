# 🏦 Explainable AI Loan Rejection Reasoner (Rural Banking)

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

**New API endpoint:** `/predict-explain`
Returns: prediction + top contributing features + plain-language reason + suggestions.

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
- [ ] (Stretch) Upgrade template-based NLG to LLM-based dynamic explanation generation
- [ ] (Stretch) Add feedback loop: track if suggested improvements actually helped reapplicants

---

### 👨‍💻 Author

Tejesh Yewale
# Right Now The Link Is Not Working 
#Deployed base system: https://loan-eligibility-ui.onrender.com/

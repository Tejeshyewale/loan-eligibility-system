# 🏦 Loan Eligibility System (ML + FastAPI + Streamlit)

A full-stack loan eligibility prediction system with:
- 🔐 JWT Authentication
- 🤖 Machine Learning Model
- ⚡ FastAPI Backend
- 🎨 Streamlit UI

## 🔧 Tech Stack
- Python
- FastAPI
- SQLAlchemy
- JWT (python-jose)
- Scikit-learn
- Streamlit

## 🚀 Features
- User signup & login
- Secure token-based authorization
- Loan eligibility prediction using 5 features:
  - Income
  - Loan Amount
  - CIBIL Score
  - Bank Assets
  - Luxury Assets
- Clean UI with instant results


### 👨‍💻 Author
Tejesh Yewale

here is the url : https://loan-eligibility-ui.onrender.com/
you can check out it's Deployed on Render...!!

## ▶ How to Run Locally

### Backend
```bash
python -m src.database.init_db
python -m uvicorn src.api.main:app --reload

###Frontend
streamlit run ui/app.py

📊 Sample Output

Loan Approved ✅
Score: 5 / 5



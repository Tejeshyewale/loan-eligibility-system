import streamlit as st
import requests

# ---------------- CONFIG ----------------
API_URL = "https://loan-eligibility-system-jc8x.onrender.com"

st.set_page_config(page_title="Loan Eligibility System", page_icon="🏦", layout="centered")

# ---------------- UI HEADER ----------------
st.title("🏦 Loan Eligibility System")
st.caption("Secure • Smart • ML-Driven")

st.divider()

# ---------------- LOGIN ----------------
st.subheader("🔐 Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

token = None

if st.button("Login"):
    res = requests.post(
        f"{API_URL}/auth/login",
        json={"username": username, "password": password}
    )

    if res.status_code == 200:
        token = res.json()["access_token"]
        st.session_state["token"] = token
        st.success("✅ Login successful")
    else:
        st.error("❌ Invalid credentials")

# ---------------- LOAN FORM ----------------
if "token" in st.session_state:
    st.divider()
    st.subheader("📄 Loan Application")

    col1, col2 = st.columns(2)

    with col1:
        income = st.number_input("💰 Annual Income (₹)", min_value=0, step=10000)
        loan_amount = st.number_input("🏦 Loan Amount (₹)", min_value=0, step=10000)
        cibil_score = st.slider("📊 CIBIL Score", 300, 900, 700)

    with col2:
        bank_assets = st.number_input("🏛️ Bank Assets (₹)", min_value=0, step=10000)
        luxury_assets = st.number_input("🚗 Luxury Assets (₹)", min_value=0, step=10000)

    if st.button("🔍 Check Eligibility"):
        headers = {
            "Authorization": f"Bearer {st.session_state['token']}"
        }

        payload = {
            "income": income,
            "loan_amount": loan_amount,
            "cibil_score": cibil_score,
            "bank_assets": bank_assets,
            "luxury_assets": luxury_assets
        }

        res = requests.post(
            f"{API_URL}/predict",
            json=payload,
            headers=headers
        )

        if res.status_code == 200:
            data = res.json()

            st.divider()
            st.subheader("📊 Result")

            if data["loan_approved"]:
                st.success("✅ Loan Approved")
            else:
                st.error("❌ Loan Rejected")

            st.metric("⭐ Eligibility Score", data["score"])

            st.markdown("### 🧾 Evaluation Summary")
            for k, v in data["criteria"].items():
                st.write(f"- **{k}**: {v}")

        else:
            st.error("⚠️ Prediction failed. Please try again.")


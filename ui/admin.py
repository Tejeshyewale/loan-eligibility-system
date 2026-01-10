import streamlit as st
import requests

API = "http://127.0.0.1:8000"

st.title("🔐 Admin Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    r = requests.post(f"{API}/auth/login",
                      params={"username": username, "password": password})
    if r.status_code == 200:
        st.session_state["token"] = r.json()["access_token"]
        st.success("Login successful")
    else:
        st.error("Login failed")

if "token" in st.session_state:
    st.subheader("📊 Loan Applications")

    apps = requests.get(f"{API}/admin/applications").json()

    for a in apps:
        st.write(a)
        col1, col2 = st.columns(2)
        if col1.button(f"Approve {a['id']}"):
            requests.post(f"{API}/admin/approve/{a['id']}")
        if col2.button(f"Reject {a['id']}"):
            requests.post(f"{API}/admin/reject/{a['id']}")

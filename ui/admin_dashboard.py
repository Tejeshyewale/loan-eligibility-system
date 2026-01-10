st.title("📊 Admin Loan Review Dashboard")

headers = {
    "Authorization": f"Bearer {st.session_state['token']}"
}

apps = requests.get(
    "http://127.0.0.1:8000/admin/applications",
    headers=headers
).json()

for app in apps:
    st.write(app)
    if st.button(f"Approve {app['id']}"):
        requests.post(f"/admin/approve/{app['id']}", headers=headers)


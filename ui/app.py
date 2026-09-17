import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import streamlit as st
import requests
from dotenv import load_dotenv
from requests.exceptions import ConnectionError, Timeout

load_dotenv()

# ---------------- CONFIG ----------------
# Local default; set API_URL in .env (or env) to the Render backend in production.
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 60

BRAND = "#0F766E"
INK = "#1F2937"
MUTED = "#6B7280"
GREEN_APPROVE = "#059669"
RED_REJECT = "#DC2626"

# ---------------- LUCIDE ICON SYSTEM (inline SVG, no emoji) ----------------
# Lucide icons (ISC/MIT licensed): 24x24, stroke-based, rendered inline.
# Consistent size 18-20px, stroke-width 2, teal (#0F766E) for primary,
# neutral gray (#6B7280) for non-primary.
ICON_PATHS = {
    # header / bank
    "bank": '<path d="M3 21h18"/><path d="M5 21V10m4 11V10m6 11V10m4 11V10"/>'
            '<path d="m12 3 9 5H3l9-5z"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/>'
            '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "user-plus": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
                 '<circle cx="9" cy="7" r="4"/>'
                 '<line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "sparkles": '<path d="M12 3v3m0 12v3M5.6 5.6l2.2 2.2m8.4 8.4 2.2 2.2M3 12h3m12 0h3M5.6 18.4l2.2-2.2m8.4-8.4 2.2-2.2"/>'
                '<circle cx="12" cy="12" r="3"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
             '<circle cx="9" cy="7" r="4"/>'
             '<path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "graduation-cap": '<path d="M22 10 12 5 2 10l10 5 10-5z"/>'
                      '<path d="M6 12v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5"/>'
                      '<path d="M22 10v6"/>',
    "briefcase": '<rect x="2" y="7" width="20" height="14" rx="2"/>'
                 '<path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    "bar-chart": '<line x1="12" x2="12" y1="20" y2="10"/>'
                 '<line x1="18" x2="18" y1="20" y2="4"/>'
                 '<line x1="6" x2="6" y1="20" y2="16"/>',
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
            '<polyline points="9 22 9 12 15 12 15 22"/>',
    "building-2": '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/>'
                  '<path d="M2 22h20"/><path d="M10 6h1m2 0h1m-4 4h1m2 0h1m-4 4h1m2 0h1"/>',
    "car": '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/>'
           '<circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/>',
    "landmark": '<line x1="3" x2="21" y1="22" y2="22"/>'
                '<line x1="6" x2="6" y1="18" y2="11"/>'
                '<line x1="10" x2="10" y1="18" y2="11"/>'
                '<line x1="14" x2="14" y1="18" y2="11"/>'
                '<line x1="18" x2="18" y1="18" y2="11"/>'
                '<polygon points="12 2 20 7 4 7"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "x-circle": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/>',
    "lightbulb": '<path d="M9 18h6M10 22h4"/>'
                 '<path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.4 1 2.3h6c0-.9.4-1.8 1-2.3A7 7 0 0 0 12 2z"/>',
    "trending-up": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>'
                   '<polyline points="16 7 22 7 22 13"/>',
    "log-out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
               '<polyline points="16 17 21 12 16 7"/>'
               '<line x1="21" x2="9" y1="12" y2="12"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
                 '<polyline points="14 2 14 8 20 8"/>'
                 '<line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/>',
    "wallet": '<path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/>'
              '<path d="M3 5v14a2 2 0 0 0 2 2h16V7"/>'
              '<circle cx="16.5" cy="14.5" r=".5"/>',
}


def icon(name, size=19, color=BRAND):
    """Inline Lucide SVG icon. Single self-contained element (no empty wrappers)."""
    inner = ICON_PATHS.get(name, ICON_PATHS["file-text"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-3px;">{inner}</svg>'
    )


TEAL = BRAND
GRAY = MUTED

# ---------------- SHARED CSS ----------------
# NOTE: cards are rendered via st.container(border=True) and styled through
# the [data-testid="stVerticalBlockBorderWrapper"] selector below — never via
# split open/close <div class="card"> markdown, which Streamlit renders as
# empty cards (each st.markdown is an isolated element, so a lone opening
# <div> auto-closes into an empty white bar).
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@600;700;800&display=swap');

html, body, [class*="st-"], .stMarkdown, .stText, p, label, div {
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;
}
h1, h2, h3, .h1-hero, .h2-section, .h3-card {
    font-family: 'Manrope', 'Inter', sans-serif !important;
}

/* Streamlit's own chrome icons (sidebar collapse toggle, expander chevrons,
   selectbox arrows, alert icons) render as Material Symbols *ligatures* in
   spans tagged data-testid="stIconMaterial" (bundled font
   MaterialSymbols-Rounded.woff2, NOT a CDN). The Inter override above matches
   those spans via their st-emotion-cache-* classes and would otherwise swap
   the icon font for Inter, leaking literal names such as
   "keyboard_double_arrow_right" / "expand_more" as visible text — and that
   stray text inside expander headers is what overlaps the label. Restore the
   icon font here (higher specificity + !important beats the blanket rule). */
span[data-testid="stIconMaterial"] {
    font-family: 'Material Symbols Rounded' !important;
    font-weight: 400 !important;
    font-style: normal !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    font-feature-settings: 'liga' !important;
    -webkit-font-feature-settings: 'liga' !important;
    -moz-font-feature-settings: 'liga' !important;
    -webkit-font-smoothing: antialiased !important;
    user-select: none !important;
    flex-shrink: 0 !important;
}

/* Type scale */
.h1-hero { font-size: 32px; font-weight: 800; line-height: 1.2; margin: 0 0 4px 0; color: #FFFFFF; }
.h2-section { font-size: 22px; font-weight: 700; line-height: 1.3; margin: 0 0 2px 0; color: #0F766E; }
.h3-card { font-size: 16px; font-weight: 600; line-height: 1.4; margin: 0 0 2px 0; color: #0F766E; }
.body-text { font-size: 14px; font-weight: 400; line-height: 1.55; color: #1F2937; }
.caption-text { font-size: 12px; font-weight: 400; line-height: 1.5; color: #6B7280; }

.block-container { max-width: 880px; padding-top: 2rem; }
.hero {
    background: linear-gradient(135deg, #0F766E 0%, #115E59 60%, #134E4A 100%);
    border-radius: 16px; padding: 28px 32px; margin-bottom: 24px;
    color: #FFFFFF; box-shadow: 0 8px 24px rgba(15,118,110,.25);
    display: flex; gap: 14px; align-items: flex-start;
}
.hero-sub { color: #D7EFED; margin: 0; font-size: 14px; font-family: 'Inter', sans-serif; }
.hero-icon { flex-shrink: 0; margin-top: 2px; }

/* Real Streamlit bordered containers -> card look (no empty divs possible) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px;
    box-shadow: 0 2px 10px rgba(31,41,55,.06); margin-bottom: 20px;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 6px 8px;
}
.card-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }

.stButton > button {
    background: #0F766E; color: #FFFFFF; border: none; border-radius: 10px;
    padding: .55rem 1.4rem; font-weight: 600; width: 100%;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important;
}
.stButton > button:hover { background: #0D6B5F; color: #FFFFFF; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-family: 'Inter', sans-serif !important; }
.stMetric { background: #F4F6F8; border-radius: 10px; padding: 8px 12px; }
small.dim { color: #6B7280; }
.stExpander { border: 1px solid #E5E7EB; border-radius: 10px; margin-bottom: 10px; }
/* Expander headers are a flex row: [chevron icon][label]. Keep them vertically
   centered with breathing room so the chevron can never sit on top of the
   label text, even before webfonts finish loading. */
[data-testid="stExpander"] summary {
    align-items: center !important;
    column-gap: 8px !important;
}
[data-testid="stExpander"] summary p {
    margin: 0 !important;
}
</style>
"""


def build_shap_chart(reasons_detail):
    """Horizontal bar chart: green = approving, red = rejecting, sorted by impact.

    Minimal data-ink styling: transparent background matching the card,
    only bottom spine visible, light gridlines, Inter font.
    """
    items = sorted(reasons_detail, key=lambda d: abs(d["shap_value"]))
    labels = [d["feature"].replace("_", " ") for d in items]
    values = [d["shap_value"] for d in items]
    colors = [GREEN_APPROVE if v >= 0 else RED_REJECT for v in values]

    plt.rcParams["font.family"] = "DejaVu Sans"  # clean Inter-like sans-serif
    fig, ax = plt.subplots(figsize=(8, max(3, 0.7 * len(items))))
    fig.patch.set_facecolor("none")
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    y_pos = range(len(items))
    bars = ax.barh(list(y_pos), values, color=colors, height=0.55, edgecolor="none")
    for bar, v in zip(bars, values):
        if v != 0:
            ax.text(
                v + (0.02 * max(abs(min(values, default=1)), abs(max(values, default=1)), 1)
                     if v >= 0 else v - 0.02 * max(abs(min(values, default=1)), abs(max(values, default=1)), 1)),
                bar.get_y() + bar.get_height() / 2,
                f"{v:+.2f}",
                va="center",
                ha="left" if v >= 0 else "right",
                fontsize=9,
                color=MUTED,
            )
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=10, color=INK)
    ax.tick_params(axis="x", labelsize=9, colors=MUTED)
    ax.tick_params(axis="y", length=0)

    # Remove top/right/left spines; keep only a light bottom axis line
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#E5E7EB")
    ax.spines["bottom"].set_linewidth(1)

    ax.axvline(0, color="#9CA3AF", linewidth=0.8)
    ax.set_xlabel("SHAP value (positive = toward approval)", fontsize=10, color=MUTED)
    ax.set_title("Feature contributions to this decision", fontsize=12, color=INK, pad=12)
    ax.xaxis.grid(True, color="#F1F5F9", linewidth=0.7, linestyle="-")
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig


def api_error_message(res=None, exc=None):
    if exc is not None and isinstance(exc, (ConnectionError, Timeout)):
        return "Cannot reach the API. Please check your connection or try again later."
    if res is not None and res.status_code == 401:
        return "Session expired or not logged in. Please log in again."
    if res is not None and res.status_code == 429:
        return "Too many requests. Please wait a minute and try again."
    return "Request failed. Please try again."


def do_login(username, password):
    res = requests.post(
        f"{API_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=REQUEST_TIMEOUT,
    )
    return res


def do_signup(username, password):
    res = requests.post(
        f"{API_URL}/auth/signup",
        json={"username": username, "password": password},
        timeout=REQUEST_TIMEOUT,
    )
    return res


def card_heading(icon_name, title, subtitle=None, icon_color=TEAL):
    """Single self-contained HTML block: icon + H3 title (+ optional caption).

    Everything opens AND closes in this one markdown string, so it can never
    produce an empty card div.
    """
    sub = f"<div class='caption-text'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"<div class='card-title-row'>{icon(icon_name, size=19, color=icon_color)}"
        f"<span class='h3-card'>{title}</span></div>{sub}",
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Loan Eligibility System", layout="centered")
st.markdown(APP_CSS, unsafe_allow_html=True)

# ---------------- HERO (single self-contained block — no split divs) ----------------
st.markdown(
    f"<div class='hero'><span class='hero-icon'>{icon('bank', size=32, color='#FFFFFF')}</span>"
    f"<span><div class='h1-hero'>Loan Eligibility System</div>"
    f"<p class='hero-sub'>Secure &bull; Smart &bull; ML-Driven — know your approval odds and why.</p></span></div>",
    unsafe_allow_html=True,
)

# ---------------- AUTH CARD ----------------
if "token" not in st.session_state:
    with st.container(border=True):
        card_heading("lock", "Welcome", "Log in to your account, or create one to get started.")
        auth_tab_login, auth_tab_signup = st.tabs(["Login", "Sign Up"])

        with auth_tab_login:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", key="login_btn"):
                if not username or not password:
                    st.warning("Please enter both username and password.")
                else:
                    try:
                        res = do_login(username, password)
                        if res.status_code == 200:
                            st.session_state["token"] = res.json()["access_token"]
                            st.success("Login successful")
                            st.rerun()
                        else:
                            st.error(api_error_message(res))
                    except (ConnectionError, Timeout) as exc:
                        st.error(api_error_message(exc=exc))

        with auth_tab_signup:
            new_user = st.text_input("Choose a username", key="signup_user")
            new_pass = st.text_input("Choose a password", type="password", key="signup_pass")
            st.caption("Accounts are secured with bcrypt-hashed passwords.")
            if st.button("Create account", key="signup_btn"):
                if not new_user or not new_pass:
                    st.warning("Please choose both a username and a password.")
                else:
                    try:
                        res = do_signup(new_user, new_pass)
                        if res.status_code == 200:
                            st.success("Account created — now log in via the Login tab.")
                        elif res.status_code == 400:
                            st.warning("That username is taken. Try another one.")
                        else:
                            st.error(api_error_message(res))
                    except (ConnectionError, Timeout) as exc:
                        st.error(api_error_message(exc=exc))

# ---------------- APP TABS ----------------
if "token" in st.session_state:
    with st.sidebar:
        st.markdown(
            f"<div class='card-title-row'>{icon('bank', size=19, color=TEAL)}"
            f"<span class='h3-card'>Loan Eligibility</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<span class='caption-text'>Secure &bull; Smart &bull; ML-Driven</span>",
                    unsafe_allow_html=True)
        st.divider()
        st.markdown("<span class='h3-card'>Session</span>", unsafe_allow_html=True)
        st.markdown("<span class='caption-text'>Logged in — session active.</span>",
                    unsafe_allow_html=True)
        st.divider()
        st.markdown("<span class='h3-card'>What to do</span>", unsafe_allow_html=True)
        st.markdown(
            "<span class='caption-text'><b>Quick Check</b> — five-field instant "
            "heuristic verdict.<br><b>Explainable AI</b> — full application with "
            "reasons and improvement tips.</span>",
            unsafe_allow_html=True,
        )
        st.divider()
        if st.button("Log out"):
            del st.session_state["token"]
            st.rerun()
        st.caption("Demo build — approvals are model estimates, not bank offers.")

    tab_quick, tab_explain = st.tabs(["Quick Check", "Explainable AI"])

    # ---------------- TAB 1: existing /predict flow (unchanged logic) ----------------
    with tab_quick:
        with st.container(border=True):
            card_heading(
                "zap", "Loan Application",
                "Five-field instant heuristic check.",
            )

            col1, col2 = st.columns(2)

            with col1:
                income = st.number_input("Annual Income (Rs.)", min_value=0, step=10000)
                loan_amount = st.number_input("Loan Amount (Rs.)", min_value=0, step=10000)
                cibil_score = st.slider("CIBIL Score", 300, 900, 700)

            with col2:
                bank_assets = st.number_input("Bank Assets (Rs.)", min_value=0, step=10000)
                luxury_assets = st.number_input("Luxury Assets (Rs.)", min_value=0, step=10000)

            if st.button("Check Eligibility"):
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

                try:
                    with st.spinner("Checking eligibility..."):
                        res = requests.post(
                            f"{API_URL}/predict",
                            json=payload,
                            headers=headers,
                            timeout=REQUEST_TIMEOUT,
                        )

                    if res.status_code == 200:
                        data = res.json()

                        st.divider()
                        st.markdown(
                            f"<div class='card-title-row'>{icon('bar-chart', size=19, color=TEAL)}"
                            f"<span class='h3-card'>Result</span></div>",
                            unsafe_allow_html=True,
                        )

                        if data["loan_approved"]:
                            st.success("Loan Approved")
                        else:
                            st.error("Loan Rejected")

                        st.metric("Eligibility Score", data["score"])

                        st.markdown("<span class='h3-card'>Evaluation Summary</span>", unsafe_allow_html=True)
                        for k, v in data["criteria"].items():
                            st.write(f"- **{k}**: {v}")
                    else:
                        st.error(api_error_message(res))
                except (ConnectionError, Timeout) as exc:
                    st.error(api_error_message(exc=exc))

    # ---------------- TAB 2: /predict-explain flow (unchanged logic) ----------------
    with tab_explain:
        with st.container(border=True):
            card_heading(
                "sparkles", "Explainable Loan Decision",
                "Full application: prediction plus reasons and how to improve.",
            )

            # Progressive disclosure: 3 logical groups, ONE submit button at the end.
            with st.expander("Personal Details", expanded=True):
                st.markdown("<span class='caption-text'>Who is applying.</span>", unsafe_allow_html=True)
                no_of_dependents = st.number_input("Dependents", min_value=0, step=1)
                education = st.selectbox("Education", ["Graduate", "Not Graduate"])
                self_employed = st.selectbox("Self Employed", ["Yes", "No"])
            with st.expander("Loan Details", expanded=True):
                st.markdown("<span class='caption-text'>Income, requested loan, and credit history.</span>",
                            unsafe_allow_html=True)
                income_annum = st.number_input("Annual Income (Rs.)", min_value=0, step=10000, key="ex_income")
                loan_amount_ex = st.number_input("Loan Amount (Rs.)", min_value=0, step=10000, key="ex_loan")
                loan_term = st.number_input("Loan Term (years)", min_value=1, step=1)
                cibil_ex = st.slider("CIBIL Score", 300, 900, 700, key="ex_cibil")
            with st.expander("Assets", expanded=True):
                st.markdown("<span class='caption-text'>What backs the application.</span>", unsafe_allow_html=True)
                residential_assets = st.number_input("Residential Assets (Rs.)", min_value=0, step=10000)
                commercial_assets = st.number_input("Commercial Assets (Rs.)", min_value=0, step=10000)
                luxury_assets_ex = st.number_input("Luxury Assets (Rs.)", min_value=0, step=10000, key="ex_luxury")
                bank_asset_value = st.number_input("Bank Assets (Rs.)", min_value=0, step=10000, key="ex_bank")

            if st.button("Explain My Decision", key="explain_btn"):
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                payload = {
                    "no_of_dependents": no_of_dependents,
                    "education": education,
                    "self_employed": self_employed,
                    "income_annum": income_annum,
                    "loan_amount": loan_amount_ex,
                    "loan_term": loan_term,
                    "cibil_score": cibil_ex,
                    "residential_assets_value": residential_assets,
                    "commercial_assets_value": commercial_assets,
                    "luxury_assets_value": luxury_assets_ex,
                    "bank_asset_value": bank_asset_value,
                }

                try:
                    with st.spinner("Analyzing your application..."):
                        res = requests.post(
                            f"{API_URL}/predict-explain",
                            json=payload,
                            headers=headers,
                            timeout=REQUEST_TIMEOUT,
                        )

                    if res.status_code != 200:
                        st.error(api_error_message(res))
                    else:
                        data = res.json()
                        with st.container(border=True):
                            if data["prediction"] == "Approved":
                                st.success(f"Loan Approved — confidence {data['probability']:.0%}")
                            else:
                                st.error(f"Loan Rejected — approval chance {data['probability']:.0%}")

                            st.markdown(
                                f"<div class='card-title-row'>{icon('bar-chart', size=19, color=TEAL)}"
                                f"<span class='h3-card'>Why this decision</span></div>",
                                unsafe_allow_html=True,
                            )
                            st.pyplot(build_shap_chart(data["reasons_detail"]))

                        with st.container(border=True):
                            st.markdown(
                                f"<div class='card-title-row'>{icon('lightbulb', size=19, color=TEAL)}"
                                f"<span class='h3-card'>Plain-language reasons</span></div>",
                                unsafe_allow_html=True,
                            )
                            for reason in data["top_reasons"]:
                                st.info(reason)

                        with st.container(border=True):
                            st.markdown(
                                f"<div class='card-title-row'>{icon('trending-up', size=19, color=TEAL)}"
                                f"<span class='h3-card'>How to improve</span></div>",
                                unsafe_allow_html=True,
                            )
                            for i, tip in enumerate(data["suggestions"], 1):
                                st.success(f"**{i}.** {tip}")
                except (ConnectionError, Timeout) as exc:
                    st.error(api_error_message(exc=exc))

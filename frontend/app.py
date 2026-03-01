"""
AURA – Login / Register Gate (Microsoft Fluent Blue Design)
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils import api_client
from utils.session_state import init_common_state, set_user, is_logged_in
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="AURA – AI Healthcare Platform",
    page_icon="⚕️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

init_common_state()
render_sidebar()

if is_logged_in():
    st.switch_page("pages/1_Dashboard.py")

# ── Hero Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2rem 0 1.5rem;">
    <div style="font-size:3.5rem; margin-bottom:0.3rem;">⚕️</div>
    <h1 style="font-size:2.4rem; font-weight:700; color:#0078D4; margin:0;">AURA</h1>
    <p style="font-size:1rem; color:#605E5C; margin:0.3rem 0 0;">AI-Powered Clinical Intelligence Platform</p>
    <div style="display:flex; justify-content:center; gap:1.5rem; margin-top:1rem; flex-wrap:wrap;">
        <span style="font-size:0.8rem; color:#0078D4;">🧠 Specialist Agents</span>
        <span style="font-size:0.8rem; color:#0078D4;">🔬 Diagnostic Imaging</span>
        <span style="font-size:0.8rem; color:#0078D4;">👨‍⚕️ Virtual Doctor</span>
        <span style="font-size:0.8rem; color:#0078D4;">🎤 Audio Mode</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Auth Card ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown("""
<div style="background:white; border:1px solid #E1DFDD; border-radius:8px;
            box-shadow:0 4px 16px rgba(0,0,0,0.08); padding:1.5rem 2rem; margin-top:0.5rem;">
""", unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])

    with tab_login:
        with st.form("login_form"):
            email    = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit   = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submit:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                with st.spinner("Authenticating..."):
                    resp = api_client.login(email, password)
                if resp.status_code == 200:
                    token = resp.json()["access_token"]
                    st.session_state.token = token
                    me_resp = api_client.get_me()
                    if me_resp.status_code == 200:
                        set_user(token, me_resp.json())
                        st.success("Welcome back! Redirecting...")
                        st.switch_page("pages/1_Dashboard.py")
                    else:
                        st.error("Could not retrieve user profile.")
                else:
                    try:
                        detail = resp.json().get("detail", "Sign-in failed")
                    except Exception:
                        detail = f"Sign-in failed (HTTP {resp.status_code})"
                    st.error(f"❌ {detail}")

    with tab_register:
        with st.form("register_form"):
            full_name    = st.text_input("Full name", placeholder="Jane Doe")
            reg_email    = st.text_input("Email address", placeholder="you@example.com", key="reg_email")
            reg_password = st.text_input("Password", type="password",
                                         placeholder="Minimum 8 characters", key="reg_pass")
            reg_submit   = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if reg_submit:
            if not full_name or not reg_email or not reg_password:
                st.error("Please fill in all fields.")
            elif len(reg_password) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                with st.spinner("Creating your account..."):
                    resp = api_client.register(reg_email, reg_password, full_name)
                if resp.status_code == 201:
                    st.success("✅ Account created. Please sign in.")
                else:
                    try:
                        detail = resp.json().get("detail", "Registration failed")
                    except Exception:
                        detail = f"Registration failed (HTTP {resp.status_code})"
                    st.error(f"❌ {detail}")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    "<center><small style='color:#A19F9D;'>AURA © 2026 · AI Healthcare Platform · "
    "Not a substitute for professional medical advice</small></center>",
    unsafe_allow_html=True
)

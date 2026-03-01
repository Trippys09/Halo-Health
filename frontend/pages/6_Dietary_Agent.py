"""
AURA – Dietary Advisor Page
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from components.auth_guard import require_login
from components.sidebar import render_sidebar
from components.chat_ui import render_chat_history
from utils.session_state import init_common_state
from utils import api_client

st.set_page_config(page_title="Dietary Advisor – AURA", page_icon="🥗", layout="wide")
init_common_state()
require_login()
render_sidebar()

st.title("🥗 Dietary Advisor")
st.caption("NORA – Personalised nutrition plans backed by science.")
st.markdown(
    "> *Share your health goals, restrictions, and lifestyle. NORA will build a tailored meal plan with detailed calorie and macro breakdowns.*"
)

# ── Session ────────────────────────────────────────────────────────────────────
if "diet_session_id" not in st.session_state:
    resp = api_client.create_session("dietary", "Dietary Advisor Session")
    st.session_state.diet_session_id = resp.json()["id"] if resp.status_code == 201 else None
    st.session_state.diet_messages = []

SESSION_ID = st.session_state.diet_session_id

col1, col2 = st.columns([4, 1])
with col2:
    if st.button("➕ New Session", use_container_width=True):
        resp = api_client.create_session("dietary", "Dietary Advisor Session")
        st.session_state.diet_session_id = resp.json()["id"] if resp.status_code == 201 else None
        st.session_state.diet_messages = []
        st.rerun()

if "diet_messages" not in st.session_state:
    msgs_resp = api_client.get_session_messages(SESSION_ID)
    st.session_state.diet_messages = (
        [{"role": m["role"], "content": m["content"]} for m in msgs_resp.json()]
        if msgs_resp.status_code == 200 else []
    )

render_chat_history(st.session_state.diet_messages)

if not st.session_state.diet_messages:
    with st.chat_message("assistant", avatar="🥗"):
        st.markdown(
            "Hello! I'm **NORA**, your personal dietary advisor. 🌿\n\n"
            "Let's create your perfect nutrition plan! To get started, could you share:\n"
            "- Your main health goal (weight loss, muscle gain, managing a condition, etc.)\n"
            "- Any dietary restrictions or allergies\n"
            "- Your activity level\n\n"
            "The more you share, the more personalised your plan will be!"
        )

if prompt := st.chat_input("Tell me about your diet goals or ask for meal ideas..."):
    st.session_state.diet_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.spinner("🥗 NORA is crafting your nutrition plan..."):
        resp = api_client.dietary_chat(SESSION_ID, prompt)

    if resp.status_code == 200:
        reply = resp.json()["reply"]
        st.session_state.diet_messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant", avatar="🥗"):
            st.markdown(reply)
    else:
        st.error("Dietary Agent unavailable. Please try again.")

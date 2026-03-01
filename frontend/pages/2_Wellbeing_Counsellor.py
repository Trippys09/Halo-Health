"""
AURA – Wellbeing Counsellor Page
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from components.auth_guard import require_login
from components.sidebar import render_sidebar
from components.chat_ui import render_chat_history
from utils.session_state import init_common_state
from utils import api_client

st.set_page_config(page_title="Wellbeing Counsellor – AURA", page_icon="💚", layout="wide")
init_common_state()
require_login()
render_sidebar()

st.title("💚 Personal Wellbeing Counsellor")
st.caption("SAGE – Your empathetic AI companion for mental wellness.")
st.markdown(
    "> *Talk freely. SAGE listens without judgment and provides evidence-based support for stress, anxiety, and low mood.*"
)

# ── Session Management ─────────────────────────────────────────────────────────
session_id = st.session_state.get("current_session_id")


def _start_new_session():
    resp = api_client.create_session("wellbeing", "New Wellbeing Session")
    if resp.status_code == 201:
        st.session_state.current_session_id = resp.json()["id"]
        st.session_state.wellbeing_messages = []
        st.rerun()
    else:
        st.error("Could not create session.")


col1, col2 = st.columns([4, 1])
with col2:
    if st.button("➕ New Session", use_container_width=True):
        _start_new_session()

if not session_id or st.session_state.get("resume_agent") not in (None, "wellbeing"):
    _start_new_session()

# Load existing messages on first render
if "wellbeing_messages" not in st.session_state:
    resp = api_client.get_session_messages(session_id)
    if resp.status_code == 200:
        msgs = resp.json()
        st.session_state.wellbeing_messages = [
            {"role": m["role"], "content": m["content"]} for m in msgs
        ]
    else:
        st.session_state.wellbeing_messages = []

# Display history
render_chat_history(st.session_state.wellbeing_messages)

if not st.session_state.wellbeing_messages:
    with st.chat_message("assistant", avatar="💚"):
        st.markdown(
            "Hello! I'm **SAGE**, your personal wellbeing counsellor. 😊\n\n"
            "How are you feeling today? Feel free to share anything that's on your mind — "
            "stress, anxiety, low mood, or just the need to talk."
        )

# ── Chat Input ─────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Share what's on your mind..."):
    st.session_state.wellbeing_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.spinner("💭 SAGE is listening..."):
        resp = api_client.wellbeing_chat(session_id, prompt)

    if resp.status_code == 200:
        reply = resp.json()["reply"]
        st.session_state.wellbeing_messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant", avatar="💚"):
            st.markdown(reply)
    else:
        st.error("Could not reach the Wellbeing Agent. Please try again.")

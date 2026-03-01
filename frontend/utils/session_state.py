"""
AURA – Streamlit Session State Helpers
"""
import streamlit as st


def init_common_state():
    """Initialise all common session-state keys."""
    defaults = {
        "token": None,
        "user": None,
        "current_session_id": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def is_logged_in() -> bool:
    return bool(st.session_state.get("token"))


def set_user(token: str, user: dict):
    st.session_state.token = token
    st.session_state.user = user


def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.current_session_id = None

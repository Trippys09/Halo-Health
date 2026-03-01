"""
AURA – Auth Guard Component
Call require_login() at the top of every protected page.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils.session_state import is_logged_in


def require_login():
    """Redirect to login page if user is not authenticated."""
    if not is_logged_in():
        st.error("🔒 Please log in to access this page.")
        st.page_link("app.py", label="Go to Login", icon="🏠")
        st.stop()

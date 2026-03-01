"""
AURA – Reusable Chat UI Component
"""
import streamlit as st
from typing import List, Dict


ROLE_AVATARS = {
    "user": "🧑",
    "assistant": "🤖",
    "model": "🤖",
}

ROLE_LABELS = {
    "user": "You",
    "assistant": "AURA",
    "model": "AURA",
}


def render_chat_history(messages: List[Dict]):
    """
    Render a list of message dicts.
    Each message: {role: str, content: str}
    """
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        avatar = ROLE_AVATARS.get(role, "💬")
        with st.chat_message(role, avatar=avatar):
            st.markdown(content)


def render_thinking_spinner():
    """Context manager spinner shown while agent is generating."""
    return st.spinner("🧠 Thinking...")

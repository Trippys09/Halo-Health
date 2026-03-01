"""
AURA – API Client
All HTTP calls from Streamlit pages go through this module.
"""
import requests
import streamlit as st

BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000")


def _headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ── Auth ──────────────────────────────────────────────────────────────────────

def register(email: str, password: str, full_name: str):
    return requests.post(
        f"{BACKEND_URL}/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
        timeout=15,
    )


def login(email: str, password: str):
    return requests.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )


def get_me():
    return requests.get(f"{BACKEND_URL}/auth/me", headers=_headers(), timeout=10)


# ── Sessions ──────────────────────────────────────────────────────────────────

def list_sessions():
    return requests.get(f"{BACKEND_URL}/sessions", headers=_headers(), timeout=10)


def create_session(agent_type: str, title: str = None):
    return requests.post(
        f"{BACKEND_URL}/sessions",
        json={"agent_type": agent_type, "title": title},
        headers=_headers(),
        timeout=10,
    )


def get_session_messages(session_id: int):
    return requests.get(
        f"{BACKEND_URL}/sessions/{session_id}/messages",
        headers=_headers(),
        timeout=10,
    )


# ── Agent Chats ───────────────────────────────────────────────────────────────

def wellbeing_chat(session_id: int, message: str):
    return requests.post(
        f"{BACKEND_URL}/agents/wellbeing/chat",
        json={"session_id": session_id, "message": message},
        headers=_headers(),
        timeout=60,
    )


def insurance_geodata(zip_code: str):
    return requests.get(
        f"{BACKEND_URL}/agents/insurance/geodata/{zip_code}",
        headers=_headers(),
        timeout=15,
    )


def insurance_chat(
    session_id: int,
    message: str,
    thread_id: str = None,
    user_profile: dict = None,
    conversation_history: list = None,
    is_profile_complete: bool = False,
):
    return requests.post(
        f"{BACKEND_URL}/agents/insurance/chat",
        json={
            "session_id": session_id,
            "message": message,
            "thread_id": thread_id,
            "user_profile": user_profile or {},
            "conversation_history": conversation_history or [],
            "is_profile_complete": is_profile_complete,
        },
        headers=_headers(),
        timeout=60,
    )


def diagnostic_chat(session_id: int, message: str, image_base64: str = None, image_mime: str = "image/jpeg"):
    return requests.post(
        f"{BACKEND_URL}/agents/diagnostic/chat",
        json={
            "session_id": session_id,
            "message": message,
            "image_base64": image_base64,
            "image_mime": image_mime,
        },
        headers=_headers(),
        timeout=120,
    )


def diagnostic_report_pdf(session_id: int, message: str, image_b64: str = None, mime_type: str = "image/jpeg"):
    """Request a diagnostic analysis and get the result as a PDF file."""
    return requests.post(
        f"{BACKEND_URL}/agents/diagnostic/report",
        json={
            "session_id": session_id,
            "message": message,
            "image_base64": image_b64,
            "image_mime": mime_type,
        },
        headers=_headers(),
        timeout=120,
    )


def virtual_doctor_chat(session_id: int, message: str, location: str = ""):
    return requests.post(
        f"{BACKEND_URL}/agents/virtual_doctor/chat",
        json={"session_id": session_id, "message": message, "extra": {"location": location}},
        headers=_headers(),
        timeout=60,
    )


def dietary_chat(session_id: int, message: str):
    return requests.post(
        f"{BACKEND_URL}/agents/dietary/chat",
        json={"session_id": session_id, "message": message},
        headers=_headers(),
        timeout=60,
    )


def orchestrator_chat(session_id: int, message: str, image_base64: str = None, image_mime: str = "image/jpeg"):
    return requests.post(
        f"{BACKEND_URL}/agents/orchestrator/chat",
        json={
            "session_id": session_id,
            "message": message,
            "image_base64": image_base64,
            "image_mime": image_mime,
        },
        headers=_headers(),
        timeout=120,
    )


# ── Audit ─────────────────────────────────────────────────────────────────────

def audit_stats():
    return requests.get(f"{BACKEND_URL}/audit/stats", headers=_headers(), timeout=15)


def audit_activity(limit: int = 100, agent_type: str = "all"):
    return requests.get(
        f"{BACKEND_URL}/audit/activity",
        params={"limit": limit, "agent_type": agent_type},
        headers=_headers(),
        timeout=15,
    )


def audit_system():
    return requests.get(f"{BACKEND_URL}/audit/system", headers=_headers(), timeout=10)

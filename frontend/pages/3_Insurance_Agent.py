"""
AURA – Insurance Agent Page (InsuCompass Integration)
Multi-phase flow: ZIP → Basic Profile → Chat
Adapted from the original InsuCompass Streamlit app to use AURA's auth + API.
"""
import uuid
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from components.auth_guard import require_login
from components.sidebar import render_sidebar
from utils.session_state import init_common_state
from utils import api_client

st.set_page_config(page_title="Insurance Advisor – AURA", page_icon="🧭", layout="centered")
init_common_state()
require_login()
render_sidebar()

st.title("🧭 InsuCompass – Insurance Advisor")
st.caption("Your AI guide to U.S. Health Insurance")

# ── Session-Level State ────────────────────────────────────────────────────────
if "ins_phase" not in st.session_state:
    st.session_state.ins_phase = "initial_zip"
if "ins_user_profile" not in st.session_state:
    st.session_state.ins_user_profile = {}
if "ins_chat_history" not in st.session_state:
    st.session_state.ins_chat_history = []
if "ins_thread_id" not in st.session_state:
    st.session_state.ins_thread_id = str(uuid.uuid4())
if "ins_profile_complete" not in st.session_state:
    st.session_state.ins_profile_complete = False
if "ins_session_id" not in st.session_state:
    resp = api_client.create_session("insurance", "Insurance Advisor Session")
    st.session_state.ins_session_id = resp.json()["id"] if resp.status_code == 201 else None

SESSION_ID = st.session_state.ins_session_id

# ── Phase 1: ZIP Code ──────────────────────────────────────────────────────────
def display_zip_form():
    st.header("1. Let's Start with Your Location")
    zip_code_input = st.text_input("Enter your 5-digit ZIP code:", max_chars=5, key="zip_input")
    if st.button("Verify ZIP", type="primary"):
        if len(zip_code_input) == 5 and zip_code_input.isdigit():
            with st.spinner("Verifying ZIP code..."):
                geo_resp = api_client.insurance_geodata(zip_code_input)
            if geo_resp.status_code == 200:
                st.session_state.ins_user_profile.update(geo_resp.json())
                st.session_state.ins_phase = "basic_profile"
                st.rerun()
            else:
                st.error("Could not verify ZIP code. Please try again.")
        else:
            st.error("Please enter a valid 5-digit ZIP code.")


# ── Phase 2: Basic Profile ─────────────────────────────────────────────────────
def display_basic_profile_form():
    st.header("2. Tell Us More About You")
    with st.form("basic_profile_form"):
        age = st.number_input("Age", min_value=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Non-binary", "Prefer not to say"])
        household_size = st.number_input("Household Size", min_value=1)
        income = st.number_input("Annual Household Income ($)", min_value=0, step=1000)
        employment_status = st.selectbox(
            "Employment Status",
            ["Employed with employer coverage", "Employed without coverage",
             "Unemployed", "Retired", "Student", "Self-employed"],
        )
        citizenship = st.selectbox(
            "Citizenship Status",
            ["US Citizen", "Lawful Permanent Resident", "Other legal resident", "Non-resident"],
        )
        submitted = st.form_submit_button("Start My Personalized Session", type="primary")
        if submitted:
            st.session_state.ins_user_profile.update({
                "age": age, "gender": gender, "household_size": household_size,
                "income": income, "employment_status": employment_status,
                "citizenship": citizenship,
                "medical_history": None, "medications": None, "special_cases": None,
            })
            st.session_state.ins_phase = "chat"
            st.rerun()


# ── Phase 3: Chat ──────────────────────────────────────────────────────────────
def display_chat():
    st.header("3. Let's Chat!")

    # Trigger initial greeting
    if not st.session_state.ins_chat_history and not st.session_state.ins_profile_complete:
        with st.spinner("Starting your personalized insurance conversation..."):
            resp = api_client.insurance_chat(
                session_id=SESSION_ID,
                message="START_PROFILE_BUILDING",
                thread_id=st.session_state.ins_thread_id,
                user_profile=st.session_state.ins_user_profile,
                conversation_history=[],
                is_profile_complete=False,
            )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.ins_user_profile = data.get("updated_profile", st.session_state.ins_user_profile)
            st.session_state.ins_chat_history = data.get("updated_history", [])
            st.session_state.ins_profile_complete = data.get("is_profile_complete", False)
            st.rerun()

    # Render history
    for message in st.session_state.ins_chat_history:
        if ":" in message:
            role, content = message.split(":", 1)
            with st.chat_message(role.lower(), avatar="🧭" if role.lower() != "user" else "🧑"):
                st.markdown(content.strip())

    if prompt := st.chat_input("Ask about insurance plans..."):
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        with st.spinner("InsuCompass AI is thinking..."):
            resp = api_client.insurance_chat(
                session_id=SESSION_ID,
                message=prompt,
                thread_id=st.session_state.ins_thread_id,
                user_profile=st.session_state.ins_user_profile,
                conversation_history=st.session_state.ins_chat_history,
                is_profile_complete=st.session_state.ins_profile_complete,
            )

        if resp.status_code == 200:
            data = resp.json()
            st.session_state.ins_user_profile = data.get("updated_profile", st.session_state.ins_user_profile)
            st.session_state.ins_chat_history = data.get("updated_history", [])
            st.session_state.ins_profile_complete = data.get("is_profile_complete", False)
            st.rerun()
        else:
            st.error("Insurance API unavailable. Please try again.")


# ── Reset ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    if st.button("🔄 Reset Insurance Session"):
        for k in ["ins_phase", "ins_user_profile", "ins_chat_history",
                  "ins_thread_id", "ins_profile_complete", "ins_session_id"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── Flow Control ───────────────────────────────────────────────────────────────
if st.session_state.ins_phase == "initial_zip":
    display_zip_form()
elif st.session_state.ins_phase == "basic_profile":
    display_basic_profile_form()
else:
    display_chat()

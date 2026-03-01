"""
AURA – Orchestrator Master Chat Page
Unified entry point routing to all specialist agents via A2A.
Includes Audio Mode.
"""
import base64
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from components.auth_guard import require_login
from components.sidebar import render_sidebar
from utils.session_state import init_common_state
from utils import api_client
from utils.audio_utils import text_to_speech

st.set_page_config(page_title="AURA Master Chat", page_icon="🧠", layout="wide")
init_common_state()
require_login()
render_sidebar()

# ── Page Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-left:4px solid #0078D4; padding:0.5rem 1rem; background:#fff; border-radius:4px; margin-bottom:1rem;">
    <h2 style="margin:0; color:#0078D4;">🧠 AURA — Master Intelligence</h2>
    <p style="margin:0; color:#605E5C; font-size:0.9rem;">Central AI hub · Routes your query to the right specialist automatically</p>
</div>
""", unsafe_allow_html=True)

# ── Agent Routing Guide ────────────────────────────────────────────────────────
with st.expander("ℹ️ Specialist agents available", expanded=False):
    st.markdown("""
| Agent | Specialty | Trigger keywords |
|---|---|---|
| **SAGE** | Mental wellness, stress, anxiety | "stressed", "anxious", "depressed", "burnout" |
| **APOLLO** | Medical consultation, symptoms, prescriptions, emergencies | "symptom", "pain", "prescription", "hospital" |
| **PRISM** | Medical imaging analysis | "scan", "x-ray", "MRI", "CT", "image" |
| **NORA** | Nutrition & meal planning | "diet", "meal", "calories", "nutrition" |
| **InsuCompass** | US health insurance | "insurance", "Medicare", "deductible", "plans" |
""")

# ── Controls Row ───────────────────────────────────────────────────────────────
col_audio, col_new = st.columns([3, 1])
with col_audio:
    audio_mode = st.toggle("🎤 Audio Mode", key="orch_audio_mode",
                           help="Speak your query — AURA will transcribe and respond in audio")
with col_new:
    if st.button("➕ New Chat", use_container_width=True):
        resp = api_client.create_session("orchestrator", "AURA Master Chat")
        st.session_state.orch_session_id = resp.json()["id"] if resp.status_code == 201 else None
        st.session_state.orch_messages = []
        st.rerun()

# ── Session ────────────────────────────────────────────────────────────────────
if "orch_session_id" not in st.session_state:
    resp = api_client.create_session("orchestrator", "AURA Master Chat")
    st.session_state.orch_session_id = resp.json()["id"] if resp.status_code == 201 else None
    st.session_state.orch_messages = []

SESSION_ID = st.session_state.orch_session_id

if "orch_messages" not in st.session_state:
    msgs_resp = api_client.get_session_messages(SESSION_ID)
    st.session_state.orch_messages = (
        [{"role": m["role"], "content": m["content"]} for m in msgs_resp.json()]
        if msgs_resp.status_code == 200 else []
    )

# ── Chat History ───────────────────────────────────────────────────────────────
for msg in st.session_state.orch_messages:
    role = msg.get("role", "user")
    avatar = "🧠" if role == "assistant" else "🧑"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.get("content", ""))

if not st.session_state.orch_messages:
    with st.chat_message("assistant", avatar="🧠"):
        st.markdown(
            "**AURA — Your AI Health Intelligence Hub**\n\n"
            "Ask me anything health-related. I coordinate with specialist agents to give you comprehensive, "
            "accurate guidance.\n\n"
            "**Example queries:**\n"
            "- *\"I have chest tightness and shortness of breath\"* → APOLLO\n"
            "- *\"I've been feeling overwhelmed and can't sleep\"* → SAGE\n"
            "- *\"Analyse this chest X-ray\"* → PRISM\n"
            "- *\"Create a high-protein meal plan for weight loss\"* → NORA\n"
            "- *\"What insurance plan suits a 35-year-old in Georgia?\"* → InsuCompass"
        )

# ── Image Upload ───────────────────────────────────────────────────────────────
with st.expander("📎 Attach a medical scan for imaging analysis (optional)"):
    uploaded_file = st.file_uploader(
        "Upload a medical scan image",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        key="orch_upload",
    )
    if uploaded_file:
        st.image(uploaded_file, caption="Attached scan", use_column_width=True)

# ── Audio Mode ─────────────────────────────────────────────────────────────────
audio_prompt = None
if audio_mode:
    st.markdown("---")
    st.markdown("**🎤 Speak your query:**")
    audio_input = st.audio_input("Record your message", key="orch_audio_input")
    if audio_input:
        with st.spinner("Transcribing audio..."):
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                audio_bytes_data = audio_input.read()
                import io
                with sr.AudioFile(io.BytesIO(audio_bytes_data)) as source:
                    audio_data = recognizer.record(source)
                audio_prompt = recognizer.recognize_google(audio_data)
                st.info(f"🗣️ Transcribed: *\"{audio_prompt}\"*")
            except Exception as e:
                st.warning(f"Transcription failed ({e}). Type your query below.")

# ── Text Chat Input ────────────────────────────────────────────────────────────
text_prompt = st.chat_input("Ask AURA anything about your health...")
prompt = audio_prompt or text_prompt

if prompt:
    st.session_state.orch_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    img_b64 = None
    img_mime = "image/jpeg"
    if uploaded_file:
        uploaded_file.seek(0)
        img_b64 = base64.b64encode(uploaded_file.read()).decode("utf-8")
        img_mime = uploaded_file.type or "image/jpeg"

    with st.spinner("🧠 AURA is coordinating with specialists..."):
        resp = api_client.orchestrator_chat(SESSION_ID, prompt, img_b64, img_mime)

    if resp.status_code == 200:
        reply = resp.json()["reply"]
        st.session_state.orch_messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(reply)

        # Audio playback
        if audio_mode:
            with st.spinner("Converting response to audio..."):
                audio_bytes = text_to_speech(reply)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
    else:
        st.error("AURA Master Chat is temporarily unavailable. Please try again.")

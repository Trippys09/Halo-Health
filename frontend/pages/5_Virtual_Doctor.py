"""
AURA – Virtual Doctor Page (APOLLO)
Includes Audio Mode: mic input → transcribe → agent → TTS playback
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from components.auth_guard import require_login
from components.sidebar import render_sidebar
from utils.session_state import init_common_state
from utils import api_client
from utils.audio_utils import text_to_speech

st.set_page_config(page_title="Virtual Doctor – AURA", page_icon="👨‍⚕️", layout="wide")
init_common_state()
require_login()
render_sidebar()

# ── Page Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-left:4px solid #0078D4; padding:0.5rem 1rem; background:#fff; border-radius:4px; margin-bottom:1rem;">
    <h2 style="margin:0; color:#0078D4;">👨‍⚕️ APOLLO — Virtual Doctor</h2>
    <p style="margin:0; color:#605E5C; font-size:0.9rem;">Medical consultation, prescriptions, nearest care, and emergency first-aid guidance</p>
</div>
<blockquote style="border-left:3px solid #D1343B; color:#D1343B; padding:0.3rem 0.8rem; background:#FFF4F4; border-radius:3px; font-size:0.85rem; margin-bottom:1rem;">
⚠️ APOLLO is an AI assistant. In a life-threatening emergency, call 911 immediately.
Prescription suggestions are AI-generated and require pharmacist or physician verification.
</blockquote>
""", unsafe_allow_html=True)

# ── Controls Row ───────────────────────────────────────────────────────────────
col_loc, col_audio, col_new = st.columns([3, 2, 1])
with col_loc:
    user_location = st.text_input(
        "📍 Your location (for nearest care search)",
        key="doc_location",
        placeholder="e.g. Atlanta, GA",
        label_visibility="collapsed",
        help="Provide your city/state for APOLLO to find nearby hospitals, urgent care, and pharmacies"
    )
with col_audio:
    audio_mode = st.toggle("🎤 Audio Mode", key="doc_audio_mode",
                           help="Enable to speak your symptoms and hear APOLLO's response")
with col_new:
    if st.button("➕ New", use_container_width=True):
        resp = api_client.create_session("virtual_doctor", "Virtual Doctor Session")
        st.session_state.doc_session_id = resp.json()["id"] if resp.status_code == 201 else None
        st.session_state.doc_messages = []
        st.rerun()

# ── Session ────────────────────────────────────────────────────────────────────
if "doc_session_id" not in st.session_state:
    resp = api_client.create_session("virtual_doctor", "Virtual Doctor Session")
    st.session_state.doc_session_id = resp.json()["id"] if resp.status_code == 201 else None
    st.session_state.doc_messages = []

SESSION_ID = st.session_state.doc_session_id

if "doc_messages" not in st.session_state:
    msgs_resp = api_client.get_session_messages(SESSION_ID)
    st.session_state.doc_messages = (
        [{"role": m["role"], "content": m["content"]} for m in msgs_resp.json()]
        if msgs_resp.status_code == 200 else []
    )

# ── Chat History ───────────────────────────────────────────────────────────────
for msg in st.session_state.doc_messages:
    role = msg.get("role", "user")
    avatar = "👨‍⚕️" if role == "assistant" else "🧑"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.get("content", ""))

if not st.session_state.doc_messages:
    with st.chat_message("assistant", avatar="👨‍⚕️"):
        st.markdown(
            "**APOLLO — Virtual Doctor**\n\n"
            "Describe your symptoms and I will provide a clinical assessment, "
            "treatment recommendations, prescription guidance, and nearest care options.\n\n"
            "*Share your location above to receive personalised facility recommendations.*"
        )

# ── Audio Mode input ───────────────────────────────────────────────────────────
audio_prompt = None
if audio_mode:
    st.markdown("---")
    st.markdown("**🎤 Speak your symptoms** — APOLLO will transcribe and respond:")
    audio_input = st.audio_input("Record your message", key="doc_audio_input")
    if audio_input:
        with st.spinner("Transcribing audio..."):
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                audio_bytes = audio_input.read()
                import io, wave
                with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                    audio_data = recognizer.record(source)
                audio_prompt = recognizer.recognize_google(audio_data)
                st.info(f"🗣️ Transcribed: *\"{audio_prompt}\"*")
            except Exception as e:
                st.warning(f"Transcription failed ({e}). Please type your symptoms below.")

# ── Text Chat Input ────────────────────────────────────────────────────────────
text_prompt = st.chat_input("Describe your symptoms or ask a medical question...")
prompt = audio_prompt or text_prompt

if prompt:
    st.session_state.doc_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.spinner("🩺 APOLLO is reviewing your case..."):
        resp = api_client.virtual_doctor_chat(
            SESSION_ID, prompt,
            location=st.session_state.get("doc_location", ""),
        )

    if resp.status_code == 200:
        reply = resp.json()["reply"]
        st.session_state.doc_messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant", avatar="👨‍⚕️"):
            st.markdown(reply)

        # Audio playback of response
        if audio_mode:
            with st.spinner("Converting response to audio..."):
                audio_bytes = text_to_speech(reply)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
    else:
        st.error("APOLLO is temporarily unavailable. Please try again.")

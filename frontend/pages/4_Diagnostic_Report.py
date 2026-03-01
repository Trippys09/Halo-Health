"""
AURA – Diagnostic Report Page (PRISM)
PDF-only export. Supports medical scan image upload.
"""
import base64
import io
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from components.auth_guard import require_login
from components.sidebar import render_sidebar
from utils.session_state import init_common_state
from utils import api_client

st.set_page_config(page_title="Diagnostic Report – AURA", page_icon="🔬", layout="wide")
init_common_state()
require_login()
render_sidebar()

# ── Page Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-left:4px solid #0078D4; padding:0.5rem 1rem; background:#fff; border-radius:4px; margin-bottom:1rem;">
    <h2 style="margin:0; color:#0078D4;">🔬 PRISM — Diagnostic Analysis</h2>
    <p style="margin:0; color:#605E5C; font-size:0.9rem;">AI-powered medical imaging and clinical diagnostic reporting</p>
</div>
<blockquote style="border-left:3px solid #D1343B; color:#D1343B; padding:0.3rem 0.8rem; background:#FFF4F4; border-radius:3px; font-size:0.85rem; margin-bottom:1rem;">
⚠️ Preliminary AI analysis only — must be reviewed by a qualified clinician.
</blockquote>
""", unsafe_allow_html=True)

# ── Session ────────────────────────────────────────────────────────────────────
if "diag_session_id" not in st.session_state:
    resp = api_client.create_session("diagnostic", "New Diagnostic Session")
    st.session_state.diag_session_id = resp.json()["id"] if resp.status_code == 201 else None
    st.session_state.diag_messages = []
    st.session_state.last_diag_reply = ""
    st.session_state.last_diag_img_b64 = None
    st.session_state.last_diag_img_mime = "image/jpeg"

SESSION_ID = st.session_state.diag_session_id

col_title, col_btn = st.columns([5, 1])
with col_btn:
    if st.button("➕ New Session", use_container_width=True):
        resp = api_client.create_session("diagnostic", "New Diagnostic Session")
        st.session_state.diag_session_id = resp.json()["id"] if resp.status_code == 201 else None
        st.session_state.diag_messages = []
        st.session_state.last_diag_reply = ""
        st.session_state.last_diag_img_b64 = None
        st.rerun()

if "diag_messages" not in st.session_state:
    msgs_resp = api_client.get_session_messages(SESSION_ID)
    st.session_state.diag_messages = (
        [{"role": m["role"], "content": m["content"]} for m in msgs_resp.json()]
        if msgs_resp.status_code == 200 else []
    )
    st.session_state.last_diag_reply = ""

# ── Image Upload ───────────────────────────────────────────────────────────────
with st.expander("📎 Upload Medical Scan (X-ray, MRI, CT, Retinal, Pathology)", expanded=True):
    uploaded_file = st.file_uploader(
        "Supported formats: JPG, PNG, BMP, TIFF",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        key="diag_upload",
    )
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded scan — ready for analysis",
                 use_column_width=False, width=420)

# ── Chat History ───────────────────────────────────────────────────────────────
for msg in st.session_state.diag_messages:
    role = msg.get("role", "user")
    avatar = "🔬" if role == "assistant" else "🧑"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.get("content", ""))

if not st.session_state.diag_messages:
    with st.chat_message("assistant", avatar="🔬"):
        st.markdown(
            "**PRISM — Diagnostic Imaging AI**\n\n"
            "Upload a medical scan above and/or describe the clinical context. "
            "I will generate a full structured diagnostic report immediately.\n\n"
            "*No need for a lengthy back-and-forth — provide what you have and I will analyse it.*"
        )

# ── Chat Input ─────────────────────────────────────────────────────────────────
prompt = st.chat_input("Describe the scan, clinical history, or ask a diagnostic question...")

if prompt:
    st.session_state.diag_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    img_b64 = None
    img_mime = "image/jpeg"
    if uploaded_file:
        uploaded_file.seek(0)
        img_b64 = base64.b64encode(uploaded_file.read()).decode("utf-8")
        img_mime = uploaded_file.type or "image/jpeg"

    with st.spinner("🔬 PRISM is generating your diagnostic report..."):
        resp = api_client.diagnostic_chat(SESSION_ID, prompt, img_b64, img_mime)

    if resp.status_code == 200:
        reply = resp.json()["reply"]
        st.session_state.diag_messages.append({"role": "assistant", "content": reply})
        st.session_state.last_diag_reply = reply
        st.session_state.last_diag_img_b64 = img_b64
        st.session_state.last_diag_img_mime = img_mime
        with st.chat_message("assistant", avatar="🔬"):
            st.markdown(reply)
    else:
        st.error(f"Diagnostic Agent error (HTTP {resp.status_code}). Please try again.")

# ── PDF Export (Diagnostic Only) ───────────────────────────────────────────────
if st.session_state.get("last_diag_reply"):
    st.divider()
    st.markdown(
        '<h4 style="color:#0078D4; margin-bottom:0.3rem;">📄 Download Medical Report</h4>',
        unsafe_allow_html=True
    )
    col_pdf, col_info = st.columns([2, 3])
    with col_pdf:
        if st.button("⬇️ Generate PDF Report", type="primary", use_container_width=True):
            with st.spinner("Building your medical PDF report..."):
                last_prompt = next(
                    (m["content"] for m in reversed(st.session_state.diag_messages) if m["role"] == "user"),
                    "Medical scan analysis"
                )
                img_b64 = st.session_state.get("last_diag_img_b64")
                img_mime = st.session_state.get("last_diag_img_mime", "image/jpeg")

                pdf_resp = api_client.diagnostic_report_pdf(
                    session_id=SESSION_ID,
                    message=last_prompt,
                    image_b64=img_b64,
                    mime_type=img_mime,
                )
            if pdf_resp.status_code == 200:
                st.download_button(
                    label="📥 Save PDF Report",
                    data=pdf_resp.content,
                    file_name=f"MEDORA_PRISM_Report_S{SESSION_ID}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
                st.success("✅ Your medical report PDF is ready.")
            else:
                st.error("PDF generation failed. The report text is shown above — copy it manually.")
    with col_info:
        st.info(
            "The PDF follows a hospital-grade format: letterhead, embedded scan image, "
            "key findings (critical findings highlighted), differential diagnoses table, "
            "severity assessment, and recommended next steps."
        )

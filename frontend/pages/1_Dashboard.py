"""
AURA – Dashboard  (Microsoft Fluent Blue Design)
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from components.auth_guard import require_login
from components.sidebar import render_sidebar
from utils.session_state import init_common_state
from utils import api_client

st.set_page_config(page_title="AURA – Dashboard", page_icon="⚕️", layout="wide")
init_common_state()
require_login()
render_sidebar()

user = st.session_state.get("user", {})
name = user.get("full_name", "there")

# ── Welcome Banner ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0078D4 0%,#005A9E 100%);
            border-radius:8px; padding:1.4rem 2rem; margin-bottom:1.5rem;
            display:flex; align-items:center; justify-content:space-between;">
    <div>
        <h2 style="color:white; margin:0; font-size:1.6rem;">Welcome back, {name} 👋</h2>
        <p style="color:#CBE4F7; margin:0.3rem 0 0; font-size:0.9rem;">
            Your AI-powered clinical intelligence platform · All systems operational
        </p>
    </div>
    <div style="font-size:3rem; opacity:0.7;">⚕️</div>
</div>
""", unsafe_allow_html=True)

# ── Agent Cards ────────────────────────────────────────────────────────────────
AGENTS = [
    {
        "key": "orchestrator",
        "title": "🧠 Master Chat",
        "desc": "Central AI hub. Routes any health query to the right specialist automatically via A2A coordination.",
        "page": "pages/7_Orchestrator_Chat.py",
        "colour": "#0078D4",
        "badge": "All Specialists",
    },
    {
        "key": "virtual_doctor",
        "title": "👨‍⚕️ Virtual Doctor",
        "desc": "Clinical consultation with APOLLO. Get assessments, prescription guidance, nearest care, and first-aid.",
        "page": "pages/5_Virtual_Doctor.py",
        "colour": "#D13438",
        "badge": "APOLLO",
    },
    {
        "key": "wellbeing",
        "title": "💚 Wellbeing Counsellor",
        "desc": "SAGE provides CBT-based support for stress, anxiety, burnout, and low mood — no judgment, just help.",
        "page": "pages/2_Wellbeing_Counsellor.py",
        "colour": "#107C10",
        "badge": "SAGE",
    },
    {
        "key": "diagnostic",
        "title": "🔬 Diagnostic Imaging",
        "desc": "PRISM analyses X-rays, MRIs, CTs, and retinal scans. Generates structured clinical reports with PDF export.",
        "page": "pages/4_Diagnostic_Report.py",
        "colour": "#8764B8",
        "badge": "PRISM",
    },
    {
        "key": "insurance",
        "title": "🧭 Insurance Advisor",
        "desc": "InsuCompass navigates ACA, Medicare, Medicaid, and employer plans. Personalised guidance for your situation.",
        "page": "pages/3_Insurance_Agent.py",
        "colour": "#005A9E",
        "badge": "InsuCompass",
    },
    {
        "key": "dietary",
        "title": "🥗 Dietary Advisor",
        "desc": "NORA creates science-backed meal plans with macro breakdowns tailored to your goals and health conditions.",
        "page": "pages/6_Dietary_Agent.py",
        "colour": "#498205",
        "badge": "NORA",
    },
]

st.markdown(
    '<div style="font-size:0.7rem; font-weight:700; color:#0078D4; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:0.8rem;">Available Agents</div>',
    unsafe_allow_html=True
)

cols = st.columns(3)
for i, agent in enumerate(AGENTS):
    with cols[i % 3]:
        st.markdown(f"""
<div style="background:white; border:1px solid #E1DFDD; border-radius:6px;
            border-top:3px solid {agent['colour']}; padding:1rem 1rem 0.6rem;
            margin-bottom:0.8rem; box-shadow:0 1px 4px rgba(0,0,0,0.07);">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.4rem;">
        <span style="font-size:1rem; font-weight:600; color:#323130;">{agent['title']}</span>
        <span style="font-size:0.65rem; background:{agent['colour']}18; color:{agent['colour']};
                     border:1px solid {agent['colour']}40; border-radius:12px; padding:1px 8px;
                     font-weight:600; white-space:nowrap;">{agent['badge']}</span>
    </div>
    <p style="font-size:0.82rem; color:#605E5C; margin:0; line-height:1.45;">{agent['desc']}</p>
</div>
""", unsafe_allow_html=True)
        if st.button("Open →", key=f"open_{agent['key']}", use_container_width=True):
            st.switch_page(agent["page"])

st.markdown("---")

# ── Recent Sessions ────────────────────────────────────────────────────────────
st.markdown(
    '<div style="font-size:0.7rem; font-weight:700; color:#0078D4; text-transform:uppercase; '
    'letter-spacing:0.07em; margin-bottom:0.6rem;">Recent Sessions</div>',
    unsafe_allow_html=True
)

EMOJI_MAP = {
    "orchestrator": "🧠", "wellbeing": "💚", "insurance": "🧭",
    "diagnostic": "🔬", "virtual_doctor": "👨‍⚕️", "dietary": "🥗",
}

try:
    resp = api_client.list_sessions()
    if resp.status_code == 200:
        sessions = resp.json()
        if not sessions:
            st.info("No sessions yet. Click an agent above to get started.")
        else:
            for sess in sessions[:6]:
                emoji = EMOJI_MAP.get(sess["agent_type"], "💬")
                title = sess.get("title") or f"{sess['agent_type'].replace('_', ' ').title()} Session"
                ts = sess.get("updated_at", "")[:16].replace("T", "  ")

                col_a, col_b = st.columns([6, 1])
                with col_a:
                    st.markdown(
                        f"<div style='background:white; border:1px solid #E1DFDD; border-radius:5px; "
                        f"padding:0.4rem 0.8rem; font-size:0.85rem; color:#323130;'>"
                        f"{emoji} <b>{title[:50]}</b> "
                        f"<span style='color:#A19F9D; font-size:0.75rem;'>· {sess['agent_type'].replace('_',' ')} · {ts}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with col_b:
                    if st.button("Resume", key=f"res_{sess['id']}", use_container_width=True):
                        st.session_state.current_session_id = sess["id"]
                        st.session_state.resume_agent = sess["agent_type"]
                        page_map = {a["key"]: a["page"] for a in AGENTS}
                        st.switch_page(page_map.get(sess["agent_type"], "pages/7_Orchestrator_Chat.py"))
    else:
        st.warning("Could not load session history.")
except Exception as e:
    st.error(f"Error loading sessions: {e}")

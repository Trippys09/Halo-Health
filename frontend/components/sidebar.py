"""
AURA – Professional Sidebar (Microsoft Fluent Blue Style)
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import api_client
from utils.session_state import logout, is_logged_in

AGENT_PAGES = {
    "orchestrator":   ("🧠 Master Chat",        "pages/7_Orchestrator_Chat.py"),
    "wellbeing":      ("💚 Wellbeing",           "pages/2_Wellbeing_Counsellor.py"),
    "insurance":      ("🧭 Insurance",           "pages/3_Insurance_Agent.py"),
    "diagnostic":     ("🔬 Diagnostic",          "pages/4_Diagnostic_Report.py"),
    "virtual_doctor": ("👨‍⚕️ Virtual Doctor",   "pages/5_Virtual_Doctor.py"),
    "dietary":        ("🥗 Dietary",             "pages/6_Dietary_Agent.py"),
}

AGENT_TYPE_EMOJI = {
    "orchestrator":   "🧠",
    "wellbeing":      "💚",
    "insurance":      "🧭",
    "diagnostic":     "🔬",
    "virtual_doctor": "👨‍⚕️",
    "dietary":        "🥗",
}


def _avatar_initials(name: str) -> str:
    parts = name.strip().split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()


def render_sidebar():
    """Render a professional Microsoft Fluent-style sidebar."""
    with st.sidebar:
        # Brand header
        st.markdown("""
<div style="background:linear-gradient(135deg,#0078D4,#005A9E); padding:1rem 0.8rem 0.8rem; border-radius:6px; margin-bottom:0.5rem;">
    <div style="display:flex; align-items:center; gap:0.5rem;">
        <span style="font-size:1.8rem;">⚕️</span>
        <div>
            <div style="color:white; font-size:1.2rem; font-weight:700; line-height:1.2;">AURA</div>
            <div style="color:#A9D3F5; font-size:0.72rem; font-weight:400;">AI Healthcare Platform</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        if is_logged_in():
            user = st.session_state.get("user", {})
            name = user.get("full_name", "User")
            email = user.get("email", "")
            initials = _avatar_initials(name)

            # User card
            st.markdown(f"""
<div style="background:#fff; border:1px solid #E1DFDD; border-radius:6px; padding:0.6rem 0.8rem; margin:0.4rem 0; display:flex; align-items:center; gap:0.6rem;">
    <div style="background:#0078D4; color:white; border-radius:50%; width:34px; height:34px; display:flex; align-items:center; justify-content:center; font-size:0.8rem; font-weight:700; min-width:34px;">{initials}</div>
    <div style="overflow:hidden;">
        <div style="font-size:0.85rem; font-weight:600; color:#323130; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{name[:22]}</div>
        <div style="font-size:0.72rem; color:#605E5C; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{email[:28]}</div>
    </div>
</div>
""", unsafe_allow_html=True)

            if st.button("🚪 Sign Out", use_container_width=True):
                logout()
                st.rerun()

            st.markdown("---")

            # ── Navigation ──────────────────────────────────────────────
            st.markdown(
                '<div style="font-size:0.7rem; font-weight:700; color:#0078D4; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.2rem;">Navigation</div>',
                unsafe_allow_html=True,
            )
            st.page_link("pages/1_Dashboard.py",            label="🏠 Home")
            st.markdown('<div style="font-size:0.65rem; color:#A19F9D; text-transform:uppercase; letter-spacing:0.05em; margin:0.3rem 0 0.1rem;">Consultation</div>', unsafe_allow_html=True)
            st.page_link("pages/7_Orchestrator_Chat.py",   label="🧠 Master Chat")
            st.page_link("pages/5_Virtual_Doctor.py",      label="👨‍⚕️ Virtual Doctor")
            st.page_link("pages/2_Wellbeing_Counsellor.py",label="💚 Wellbeing")
            st.markdown('<div style="font-size:0.65rem; color:#A19F9D; text-transform:uppercase; letter-spacing:0.05em; margin:0.3rem 0 0.1rem;">Analysis</div>', unsafe_allow_html=True)
            st.page_link("pages/4_Diagnostic_Report.py",   label="🔬 Diagnostic")
            st.page_link("pages/3_Insurance_Agent.py",     label="🧭 Insurance")
            st.markdown('<div style="font-size:0.65rem; color:#A19F9D; text-transform:uppercase; letter-spacing:0.05em; margin:0.3rem 0 0.1rem;">Wellness</div>', unsafe_allow_html=True)
            st.page_link("pages/6_Dietary_Agent.py",       label="🥗 Dietary Advisor")
            st.markdown('<div style="font-size:0.65rem; color:#A19F9D; text-transform:uppercase; letter-spacing:0.05em; margin:0.3rem 0 0.1rem;">Admin</div>', unsafe_allow_html=True)
            st.page_link("pages/8_Audit.py",               label="📊 Audit & Logs")

            st.markdown("---")

            # ── Recent Sessions ──────────────────────────────────────────
            st.markdown(
                '<div style="font-size:0.7rem; font-weight:700; color:#0078D4; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.4rem;">Recent Sessions</div>',
                unsafe_allow_html=True,
            )
            try:
                resp = api_client.list_sessions()
                if resp.status_code == 200:
                    sessions = resp.json()
                    if not sessions:
                        st.caption("No sessions yet.")
                    for sess in sessions[:8]:
                        emoji = AGENT_TYPE_EMOJI.get(sess["agent_type"], "💬")
                        label = sess.get("title") or f"{emoji} {sess['agent_type'].replace('_', ' ').title()}"
                        if st.button(
                            label[:36],
                            key=f"sess_{sess['id']}",
                            use_container_width=True,
                        ):
                            st.session_state.current_session_id = sess["id"]
                            st.session_state.resume_agent = sess["agent_type"]
                            st.rerun()
            except Exception:
                st.caption("Could not load sessions.")
        else:
            st.info("Please log in to use AURA.")

"""
AURA – Audit Dashboard Page
Shows agent interaction stats, activity feed, and system event log.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import pandas as pd
from datetime import datetime
from components.auth_guard import require_login
from components.sidebar import render_sidebar
from utils.session_state import init_common_state
from utils import api_client

st.set_page_config(page_title="Audit – AURA", page_icon="📋", layout="wide")
init_common_state()
require_login()
render_sidebar()

st.title("📋 Audit Dashboard")
st.caption("Monitor agent interactions, session activity, and system events in real time.")

# ── Agent metadata ────────────────────────────────────────────────────────────
AGENT_META = {
    "wellbeing":     {"icon": "💚", "name": "Wellbeing (SAGE)"},
    "insurance":     {"icon": "🧭", "name": "Insurance"},
    "diagnostic":    {"icon": "🔬", "name": "Diagnostic (PRISM)"},
    "virtual_doctor":{"icon": "👨‍⚕️", "name": "Virtual Doctor (APOLLO)"},
    "dietary":       {"icon": "🥗", "name": "Dietary (NORA)"},
    "orchestrator":  {"icon": "🧠", "name": "Orchestrator"},
}

LEVEL_COLOR = {"INFO": "🟢", "WARNING": "🟡", "ERROR": "🔴"}


def _agent_label(agent_type: str) -> str:
    meta = AGENT_META.get(agent_type, {"icon": "🤖", "name": agent_type.replace("_", " ").title()})
    return f"{meta['icon']} {meta['name']}"


# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner("Loading audit data..."):
    stats_resp = api_client.audit_stats()
    activity_resp = api_client.audit_activity(limit=100, agent_type="all")
    system_resp = api_client.audit_system()

stats_ok = stats_resp.status_code == 200
activity_ok = activity_resp.status_code == 200
system_ok = system_resp.status_code == 200

# ── Refresh button ────────────────────────────────────────────────────────────
col_title, col_refresh = st.columns([5, 1])
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════
tab_overview, tab_activity, tab_system = st.tabs([
    "📊 Overview", "🔍 Activity Log", "⚙️ System Events"
])

# ── TAB 1: Overview ───────────────────────────────────────────────────────────
with tab_overview:
    if not stats_ok:
        st.error("Could not load stats.")
    else:
        data = stats_resp.json()

        # KPI row
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Sessions", data.get("total_sessions", 0))
        k2.metric("Messages Sent", data.get("total_user_messages", 0))
        k3.metric("Agent Replies", data.get("total_agent_messages", 0))
        k4.metric("Avg Reply Length", f"{data.get('avg_agent_response_chars', 0):.0f} chars")
        k5.metric("Sessions (7 days)", data.get("sessions_last_7_days", 0))

        st.divider()

        # Sessions by agent
        sessions_by_agent = data.get("sessions_by_agent", [])
        if sessions_by_agent:
            st.subheader("Sessions by Agent")
            df = pd.DataFrame(sessions_by_agent)
            df["Agent"] = df["agent"].apply(_agent_label)
            df = df.rename(columns={"sessions": "Sessions"})
            df = df[["Agent", "Sessions"]].sort_values("Sessions", ascending=False)

            # Two columns: bar chart + table
            c_chart, c_table = st.columns([3, 2])
            with c_chart:
                st.bar_chart(df.set_index("Agent")["Sessions"])
            with c_table:
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No sessions recorded yet. Start chatting with any agent!")

# ── TAB 2: Activity Log ───────────────────────────────────────────────────────
with tab_activity:
    if not activity_ok:
        st.error("Could not load activity log.")
    else:
        activity = activity_resp.json()

        # Filter controls
        fc1, fc2, fc3 = st.columns([2, 2, 2])
        with fc1:
            agent_filter = st.selectbox(
                "Filter by Agent",
                ["All"] + [m["name"] for m in AGENT_META.values()],
                key="audit_agent_filter",
            )
        with fc2:
            role_filter = st.radio("Message Role", ["All", "User", "Assistant"], horizontal=True)
        with fc3:
            search_kw = st.text_input("Search content", placeholder="keyword...")

        # Apply filters
        filtered = activity
        if agent_filter != "All":
            # Match on agent display name
            matching_types = [k for k, v in AGENT_META.items() if v["name"] in agent_filter]
            filtered = [r for r in filtered if r["agent_type"] in matching_types]
        if role_filter != "All":
            filtered = [r for r in filtered if r["role"] == role_filter.lower()]
        if search_kw:
            filtered = [r for r in filtered if search_kw.lower() in r["content_preview"].lower()]

        st.caption(f"Showing {len(filtered)} of {len(activity)} interactions")
        st.divider()

        if not filtered:
            st.info("No interactions match your filters.")
        else:
            for row in filtered:
                ts = row.get("timestamp", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        ts_fmt = dt.strftime("%b %d %H:%M:%S")
                    except Exception:
                        ts_fmt = ts[:19]
                else:
                    ts_fmt = "—"

                agent_label = _agent_label(row.get("agent_type", "unknown"))
                role = row.get("role", "user")
                role_icon = "🧑" if role == "user" else "🤖"
                preview = row.get("content_preview", "")
                char_count = row.get("content_length", 0)
                sess_title = row.get("session_title", f"Session #{row.get('session_id')}")

                with st.expander(
                    f"{role_icon} **{role.upper()}** · {agent_label} · {ts_fmt} · `{char_count} chars`",
                    expanded=False,
                ):
                    st.caption(f"📂 Session: **{sess_title}** (ID: {row.get('session_id')})")
                    st.markdown(preview + ("…" if char_count > 200 else ""))

# ── TAB 3: System Events ──────────────────────────────────────────────────────
with tab_system:
    if not system_ok:
        st.error("Could not load system events.")
    else:
        events = system_resp.json()

        if not events:
            st.info("No system events yet. Events are logged on startup and during agent interactions.")
        else:
            st.caption(f"{len(events)} events recorded (newest first, max 200 kept in memory)")
            st.divider()

            for ev in events:
                level = ev.get("level", "INFO")
                icon = LEVEL_COLOR.get(level, "⚪")
                ts_raw = ev.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                    ts_fmt = dt.strftime("%H:%M:%S UTC")
                except Exception:
                    ts_fmt = ts_raw[:19]

                source = ev.get("source", "system")
                msg = ev.get("message", "")
                details = ev.get("details", "")

                col_icon, col_content = st.columns([0.5, 9.5])
                with col_icon:
                    st.markdown(f"### {icon}")
                with col_content:
                    st.markdown(f"**`{level}`** `{ts_fmt}` · **{source}**")
                    st.markdown(msg)
                    if details:
                        st.caption(details)
                st.divider()

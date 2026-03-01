"""
HALO Health – Audit Router
GET /audit/stats      – aggregate stats per agent (sessions, messages, avg response size)
GET /audit/activity   – recent agent interactions as a timeline feed
GET /audit/system     – system events (model selection, startup, errors)
"""
import logging
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.models.session import ChatSession
from backend.models.message import ChatMessage
from backend.routers.deps import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])
logger = logging.getLogger(__name__)

# ── In-memory system event log ────────────────────────────────────────────────
# Other modules append here: from backend.routers.audit import log_event
_system_events: List[dict] = []
_MAX_EVENTS = 200


def log_event(level: str, source: str, message: str, details: str = ""):
    """Append a system event. Call this from agents and services."""
    _system_events.append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level.upper(),   # INFO / WARNING / ERROR
        "source": source,
        "message": message,
        "details": details,
    })
    if len(_system_events) > _MAX_EVENTS:
        _system_events.pop(0)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/stats")
def audit_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return aggregate stats for the current user's agent interactions."""
    user_id = current_user.id

    # Sessions per agent
    sessions_by_agent = (
        db.query(ChatSession.agent_type, func.count(ChatSession.id).label("count"))
        .filter(ChatSession.user_id == user_id)
        .group_by(ChatSession.agent_type)
        .all()
    )

    # Total messages sent/received
    total_user_msgs = (
        db.query(func.count(ChatMessage.id))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .filter(ChatSession.user_id == user_id, ChatMessage.role == "user")
        .scalar() or 0
    )
    total_agent_msgs = (
        db.query(func.count(ChatMessage.id))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .filter(ChatSession.user_id == user_id, ChatMessage.role == "assistant")
        .scalar() or 0
    )

    # Average agent response length (chars)
    avg_len = (
        db.query(func.avg(func.length(ChatMessage.content)))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .filter(ChatSession.user_id == user_id, ChatMessage.role == "assistant")
        .scalar()
    )

    # Sessions in the last 7 days
    cutoff = datetime.utcnow() - timedelta(days=7)
    recent_sessions = (
        db.query(func.count(ChatSession.id))
        .filter(ChatSession.user_id == user_id, ChatSession.created_at >= cutoff)
        .scalar() or 0
    )

    return {
        "sessions_by_agent": [
            {"agent": row.agent_type, "sessions": row.count}
            for row in sessions_by_agent
        ],
        "total_user_messages": total_user_msgs,
        "total_agent_messages": total_agent_msgs,
        "avg_agent_response_chars": round(avg_len or 0, 1),
        "sessions_last_7_days": recent_sessions,
        "total_sessions": sum(r.count for r in sessions_by_agent),
    }


@router.get("/activity")
def audit_activity(
    limit: int = 50,
    agent_type: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a recent activity feed of agent interactions."""
    query = (
        db.query(ChatMessage, ChatSession)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .filter(ChatSession.user_id == current_user.id)
    )
    if agent_type and agent_type != "all":
        query = query.filter(ChatSession.agent_type == agent_type)

    rows = (
        query.order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": msg.id,
            "session_id": msg.session_id,
            "session_title": sess.title or f"Session #{sess.id}",
            "agent_type": sess.agent_type,
            "role": msg.role,
            "content_preview": (msg.content or "")[:200],
            "content_length": len(msg.content or ""),
            "timestamp": msg.created_at.isoformat() + "Z" if msg.created_at else None,
        }
        for msg, sess in rows
    ]


@router.get("/system")
def audit_system(
    current_user: User = Depends(get_current_user),
):
    """Return recent system events (model selection, errors, etc.)."""
    return list(reversed(_system_events))  # newest first

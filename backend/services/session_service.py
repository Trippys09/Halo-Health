"""
HALO Health – Session Service (CRUD for ChatSession and ChatMessage)
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models.session import ChatSession
from backend.models.message import ChatMessage


# ── Session CRUD ──────────────────────────────────────────────────────────────

def create_session(
    db: Session, user_id: int, agent_type: str, title: Optional[str] = None
) -> ChatSession:
    session = ChatSession(user_id=user_id, agent_type=agent_type, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_sessions(db: Session, user_id: int) -> List[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


def get_session(db: Session, session_id: int, user_id: int) -> Optional[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )


def update_session_title(db: Session, session: ChatSession, title: str) -> ChatSession:
    session.title = title
    db.commit()
    db.refresh(session)
    return session


# ── Message CRUD ──────────────────────────────────────────────────────────────

def add_message(
    db: Session, session_id: int, role: str, content: str, image_data: Optional[str] = None
) -> ChatMessage:
    msg = ChatMessage(session_id=session_id, role=role, content=content, image_data=image_data)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_session_messages(db: Session, session_id: int) -> List[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def get_recent_messages(
    db: Session, session_id: int, limit: int = 20
) -> List[ChatMessage]:
    """Return the most recent N messages for context injection."""
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def build_history_for_gemini(messages: List[ChatMessage]) -> List[dict]:
    """Convert DB messages to Gemini chat history format."""
    history = []
    for m in messages:
        history.append(
            {
                "role": "user" if m.role == "user" else "model",
                "parts": [{"text": m.content}],
            }
        )
    return history

"""
HALO Health – Wellbeing Agent Router
POST /agents/wellbeing/chat
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services import session_service
from backend.agents.wellbeing_agent import wellbeing_agent

router = APIRouter(prefix="/agents/wellbeing", tags=["Wellbeing Agent"])


@router.post("/chat", response_model=ChatResponse)
def wellbeing_chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sess = session_service.get_session(db, req.session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Persist user message
    session_service.add_message(db, req.session_id, "user", req.message)

    # Build history for Gemini
    messages = session_service.get_recent_messages(db, req.session_id, limit=20)
    # Exclude the message we just added (it will be passed as user_message)
    history = session_service.build_history_for_gemini(messages[:-1])

    reply = wellbeing_agent.respond(
        user_message=req.message,
        history=history,
        user_id=current_user.id,
    )

    # Persist assistant reply
    session_service.add_message(db, req.session_id, "assistant", reply)

    # Auto-title session on first exchange
    if not sess.title:
        session_service.update_session_title(
            db, sess, f"Wellbeing: {req.message[:40]}..."
        )

    return ChatResponse(session_id=req.session_id, reply=reply, agent_type="wellbeing")

"""
HALO Health – Dietary Agent Router
POST /agents/dietary/chat
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services import session_service
from backend.agents.dietary_agent import dietary_agent

router = APIRouter(prefix="/agents/dietary", tags=["Dietary Agent"])


@router.post("/chat", response_model=ChatResponse)
def dietary_chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sess = session_service.get_session(db, req.session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session_service.add_message(db, req.session_id, "user", req.message)

    messages = session_service.get_recent_messages(db, req.session_id, limit=20)
    history = session_service.build_history_for_gemini(messages[:-1])

    reply = dietary_agent.respond(
        user_message=req.message,
        history=history,
        user_id=current_user.id,
    )

    session_service.add_message(db, req.session_id, "assistant", reply)

    if not sess.title:
        session_service.update_session_title(
            db, sess, f"Dietary: {req.message[:40]}..."
        )

    return ChatResponse(session_id=req.session_id, reply=reply, agent_type="dietary")

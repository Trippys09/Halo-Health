"""
HALO Health – Orchestrator Router (Master Chat)
POST /agents/orchestrator/chat
"""
import base64

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.chat import DiagnosticChatRequest, ChatResponse
from backend.services import session_service
from backend.agents.orchestrator_agent import orchestrator_agent

router = APIRouter(prefix="/agents/orchestrator", tags=["Orchestrator"])


@router.post("/chat", response_model=ChatResponse)
def orchestrator_chat(
    req: DiagnosticChatRequest,  # reuse schema – it has optional image fields
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sess = session_service.get_session(db, req.session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session_service.add_message(db, req.session_id, "user", req.message)

    messages = session_service.get_recent_messages(db, req.session_id, limit=20)
    history = session_service.build_history_for_gemini(messages[:-1])

    image_data = None
    if req.image_base64:
        try:
            image_data = base64.b64decode(req.image_base64)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 image",
            )

    reply = orchestrator_agent.respond(
        user_message=req.message,
        history=history,
        user_id=current_user.id,
        image_data=image_data,
        mime_type=req.image_mime or "image/jpeg",
    )

    session_service.add_message(db, req.session_id, "assistant", reply)

    if not sess.title:
        session_service.update_session_title(
            db, sess, f"HALO: {req.message[:40]}..."
        )

    return ChatResponse(session_id=req.session_id, reply=reply, agent_type="orchestrator")

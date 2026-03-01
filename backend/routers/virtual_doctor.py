"""
HALO Health – Virtual Doctor Router
POST /agents/virtual_doctor/chat
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services import session_service
from backend.agents.virtual_doctor_agent import virtual_doctor_agent

router = APIRouter(prefix="/agents/virtual_doctor", tags=["Virtual Doctor"])


@router.post("/chat", response_model=ChatResponse)
def virtual_doctor_chat(
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

    user_location = ""
    if req.extra:
        user_location = req.extra.get("location", "")

    reply = virtual_doctor_agent.respond(
        user_message=req.message,
        history=history,
        user_id=current_user.id,
        user_location=user_location,
    )

    session_service.add_message(db, req.session_id, "assistant", reply)

    if not sess.title:
        session_service.update_session_title(
            db, sess, f"Doctor: {req.message[:40]}..."
        )

    return ChatResponse(session_id=req.session_id, reply=reply, agent_type="virtual_doctor")

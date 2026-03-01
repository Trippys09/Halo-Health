"""
HALO Health – Visualisation Agent Router
POST /agents/visualisation/chat
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services import session_service
from backend.agents.visualisation_agent import visualisation_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents/visualisation", tags=["Visualisation Agent"])


@router.post("/chat", response_model=ChatResponse)
def visualisation_chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chat with the Nano Banana Visualisation Agent to generate data diagrams."""
    sess = session_service.get_session(db, req.session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Save user message
    session_service.add_message(db, req.session_id, "user", req.message)

    # Fetch history
    messages = session_service.get_recent_messages(db, req.session_id, limit=20)
    history = session_service.build_history_for_gemini(messages[:-1])

    reply = visualisation_agent.respond(req.message, history, current_user.id)

    # Save agent reply
    session_service.add_message(db, req.session_id, "assistant", reply)

    # Update title
    if not sess.title or sess.title == "New Visualisation Session":
        title = req.message[:50] if req.message else "Visualisation Task"
        session_service.update_session_title(db, sess, f"Visualisation: {title}")

    return ChatResponse(session_id=req.session_id, reply=reply, agent_type="visualisation")

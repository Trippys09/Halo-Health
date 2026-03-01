"""
HALO Health – Oculomics Agent Router
POST /agents/oculomics/chat   – text + optional base64 image → Oculomics Retinal Report
"""
import base64
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.chat import DiagnosticChatRequest, OculomicsChatResponse
from backend.services import session_service
from backend.agents.oculomics_agent import oculomics_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents/oculomics", tags=["Oculomics Agent"])


def _decode_image(req: DiagnosticChatRequest):
    if not req.image_base64:
        return None
    try:
        return base64.b64decode(req.image_base64)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 image data",
        )


@router.post("/chat", response_model=OculomicsChatResponse)
def oculomics_chat(
    req: DiagnosticChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chat with Oculomics Retina engine. Optionally include a base64 fundus image."""
    sess = session_service.get_session(db, req.session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    session_service.add_message(db, req.session_id, "user", req.message, image_data=req.image_base64)

    messages = session_service.get_recent_messages(db, req.session_id, limit=20)
    history = session_service.build_history_for_gemini(messages[:-1])

    image_data = _decode_image(req)

    reply, outcomes = oculomics_agent.respond(
        user_message=req.message,
        history=history,
        user_id=current_user.id,
        image_data=image_data,
        mime_type=req.image_mime or "image/jpeg",
    )

    session_service.add_message(db, req.session_id, "assistant", reply)

    if not sess.title or sess.title == "New Diagnostic Session":
        title = req.message[:50] if req.message else "Retinal Scan Biomarker Analysis"
        session_service.update_session_title(db, sess, f"Oculomics: {title}")

    return OculomicsChatResponse(
        session_id=req.session_id, 
        reply=reply, 
        agent_type="oculomics",
        outcomes=outcomes
    )

"""
HALO Health – Diagnostic Agent Router
POST /agents/diagnostic/chat   – text + optional base64 image → diagnostic report
POST /agents/diagnostic/report – same as chat but returns PDF file download
"""
import base64
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.chat import DiagnosticChatRequest, ChatResponse
from backend.services import session_service
from backend.services.pdf_generator import generate_diagnostic_pdf
from backend.agents.diagnostic_agent import diagnostic_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents/diagnostic", tags=["Diagnostic Agent"])


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


def _run_diagnostic(req, current_user, db):
    sess = session_service.get_session(db, req.session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session_service.add_message(db, req.session_id, "user", req.message, image_data=req.image_base64)

    messages = session_service.get_recent_messages(db, req.session_id, limit=20)
    history = session_service.build_history_for_gemini(messages[:-1])

    image_data = _decode_image(req)

    reply = diagnostic_agent.respond(
        user_message=req.message,
        history=history,
        user_id=current_user.id,
        image_data=image_data,
        mime_type=req.image_mime or "image/jpeg",
    )

    session_service.add_message(db, req.session_id, "assistant", reply)

    if not sess.title or sess.title == "New Diagnostic Session":
        title = req.message[:50] if req.message else "Medical Image Analysis"
        session_service.update_session_title(db, sess, f"Diagnostic: {title}")

    return sess, reply


@router.post("/chat", response_model=ChatResponse)
def diagnostic_chat(
    req: DiagnosticChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chat with PRISM diagnostic agent. Optionally include a base64 medical image."""
    _, reply = _run_diagnostic(req, current_user, db)
    return ChatResponse(session_id=req.session_id, reply=reply, agent_type="diagnostic")


@router.post("/report")
def diagnostic_report_pdf(
    req: DiagnosticChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a diagnostic report AND return it as a downloadable PDF.
    Same request format as /chat — just downloads a PDF instead.
    """
    _, reply = _run_diagnostic(req, current_user, db)

    try:
        image_data = _decode_image(req)
        pdf_bytes = generate_diagnostic_pdf(
            report_text=reply,
            patient_name=current_user.full_name or current_user.email,
            session_id=req.session_id,
            image_data=image_data,
            image_mime=req.image_mime or "image/jpeg",
        )
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report generated but PDF export failed. Please try the chat endpoint.",
        )

    filename = f"MEDORA_Diagnostic_Report_Session{req.session_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )

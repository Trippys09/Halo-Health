"""
HALO Health – Insurance Agent Router (COMPASS Proxy)
GET  /agents/insurance/geodata/{zip_code}
POST /agents/insurance/chat
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.chat import InsuranceChatRequest, InsuranceChatResponse
from backend.services import session_service
from backend.agents.insurance_agent import insurance_agent

router = APIRouter(prefix="/agents/insurance", tags=["Insurance Agent"])


@router.get("/geodata/{zip_code}")
async def get_geodata(
    zip_code: str,
    current_user: User = Depends(get_current_user),
):
    """Proxy ZIP → geo lookup to COMPASS API."""
    data = await insurance_agent.get_geodata(zip_code)
    if not data:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="ZIP lookup failed")
    return data


@router.post("/chat", response_model=InsuranceChatResponse)
async def insurance_chat(
    req: InsuranceChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sess = session_service.get_session(db, req.session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Persist user message
    session_service.add_message(db, req.session_id, "user", req.message)

    thread_id = req.thread_id or str(uuid.uuid4())

    # Build gemini-compatible history from saved messages
    messages = session_service.get_recent_messages(db, req.session_id, limit=20)
    gemini_history = session_service.build_history_for_gemini(messages)

    result = await insurance_agent.chat(
        thread_id=thread_id,
        user_profile=req.user_profile or {},
        message=req.message,
        conversation_history=req.conversation_history or [],
        is_profile_complete=req.is_profile_complete,
        user_id=current_user.id,
        history=gemini_history,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Insurance API unavailable",
        )

    reply_text = ""
    if result.get("updated_history"):
        last = result["updated_history"][-1]
        if ":" in last:
            _, reply_text = last.split(":", 1)
            reply_text = reply_text.strip()

    # Persist assistant reply
    session_service.add_message(db, req.session_id, "assistant", reply_text)

    if not sess.title:
        session_service.update_session_title(db, sess, "Insurance Advisor Session")

    return InsuranceChatResponse(
        session_id=req.session_id,
        reply=reply_text,
        updated_profile=result.get("updated_profile"),
        updated_history=result.get("updated_history"),
        is_profile_complete=result.get("is_profile_complete", False),
    )

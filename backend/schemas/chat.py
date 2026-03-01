"""
AURA – Chat / Session Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, Any, Dict

from pydantic import BaseModel


# ── Sessions ──────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    agent_type: str
    title: Optional[str] = None


class SessionOut(BaseModel):
    id: int
    agent_type: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Messages ──────────────────────────────────────────────────────────────────

class MessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    image_data: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Generic Chat Request / Response ──────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: int
    message: str
    extra: Optional[Dict[str, Any]] = None  # Agent-specific extra payload


class ChatResponse(BaseModel):
    session_id: int
    reply: str
    agent_type: str


# ── Insurance-specific ────────────────────────────────────────────────────────

class InsuranceChatRequest(BaseModel):
    session_id: int
    message: str
    thread_id: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None
    conversation_history: Optional[list] = None
    is_profile_complete: bool = False


class InsuranceChatResponse(BaseModel):
    session_id: int
    reply: str
    agent_type: str = "insurance"
    updated_profile: Optional[Dict[str, Any]] = None
    updated_history: Optional[list] = None
    is_profile_complete: bool = False


# ── Diagnostic-specific ────────────────────────────────────────────────────────

class DiagnosticChatRequest(BaseModel):
    session_id: int
    message: str
    image_base64: Optional[str] = None   # Base64-encoded medical image
    image_mime: Optional[str] = "image/jpeg"


class OculomicsChatResponse(ChatResponse):
    outcomes: Optional[Dict[str, Any]] = None

"""
HALO Health – Sessions Router
GET  /sessions           – list current user's sessions
POST /sessions           – create a new session
GET  /sessions/{id}      – get session metadata
GET  /sessions/{id}/messages – full message history for a session
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.chat import SessionCreate, SessionOut, MessageOut
from pydantic import BaseModel
from backend.services import session_service

class SessionRename(BaseModel):
    title: str

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionOut])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return session_service.get_user_sessions(db, current_user.id)


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    req: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return session_service.create_session(db, current_user.id, req.agent_type, req.title)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sess = session_service.get_session(db, session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return sess


@router.get("/{session_id}/messages", response_model=List[MessageOut])
def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sess = session_service.get_session(db, session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session_service.get_session_messages(db, session_id)


@router.put("/{session_id}", response_model=SessionOut)
def rename_session(
    session_id: int,
    req: SessionRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sess = session_service.get_session(db, session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    sess.title = req.title
    db.commit()
    db.refresh(sess)
    return sess


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sess = session_service.get_session(db, session_id, current_user.id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    db.delete(sess)
    db.commit()
    return None

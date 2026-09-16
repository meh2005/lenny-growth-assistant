import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ChatSession, ChatMessage


router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


# ---------- Schemas ----------

class SessionCreate(BaseModel):
    user_name: str = "Guest"
    title: str = "New Chat"


class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources: list[dict] = []

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: UUID
    title: str
    user_name: str

    class Config:
        from_attributes = True


class SessionDetail(SessionResponse):
    messages: list[MessageResponse]


# ---------- Endpoints ----------

@router.post("", response_model=SessionResponse, status_code=201)
def create_session(
    data: SessionCreate,
    db: Session = Depends(get_db)
):
    session = ChatSession(
        title=data.title,
        user_name=data.user_name
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db)
):
    return (
        db.query(ChatSession)
        .order_by(ChatSession.created_at.desc())
        .all()
    )


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    for message in session.messages:
        if message.sources:
            try:
                message.sources = json.loads(message.sources)
            except json.JSONDecodeError:
                message.sources = []
        else:
            message.sources = []

    return session

@router.post(
    "/{session_id}/messages",
    response_model=MessageResponse,
    status_code=201
)
def add_message(
    session_id: UUID,
    data: MessageCreate,
    db: Session = Depends(get_db)
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    if data.role not in {"user", "assistant", "system"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid message role"
        )

    message = ChatMessage(
        session_id=session_id,
        role=data.role,
        content=data.content
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    db.delete(session)
    db.commit()

    return None

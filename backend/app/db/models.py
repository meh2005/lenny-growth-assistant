from sqlalchemy import Column, DateTime, String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

import uuid

from app.db.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    title = Column(
        String,
        default="New Chat"
    )

    user_name = Column(
        String,
        default="Guest"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id")
    )

    role = Column(String)

    content = Column(Text)

    sources = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    session = relationship(
        "ChatSession",
        back_populates="messages"
    )


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    source_id = Column(
        String,
        nullable=False,
        index=True
    )

    episode_title = Column(
        String,
        nullable=False
    )

    guest_name = Column(
        String,
        nullable=True
    )

    source_url = Column(
        String,
        nullable=True
    )

    content = Column(
        Text,
        nullable=False
    )

    chunk_index = Column(
        Integer,
        nullable=False
    )

    embedding = Column(
        Vector(384),
        nullable=False
    )
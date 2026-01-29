"""
SQLAlchemy models for Chat and Message.

These models mirror the Drizzle schema defined in client/src/db/schema.ts
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin


class Chat(Base, TimestampMixin):
    """
    Chat session model.
    
    Represents a conversation session between a user and the AI assistant.
    """
    
    __tablename__ = "chats"
    
    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True
    )
    # Note: FK to profiles.id exists in database but not enforced by SQLAlchemy
    # since profiles table is managed by Drizzle/Supabase, not this backend
    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, title='{self.title[:30]}...')>"


class Message(Base):
    """
    Chat message model.
    
    Represents a single message in a chat conversation.
    """
    
    __tablename__ = "messages"
    
    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True
    )
    chat_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(
        String(20),  # 'user', 'assistant', 'system'
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",  # Database column name stays 'metadata'
        JSON,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    # Relationships
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="messages"
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role='{self.role}')>"

"""
SQLAlchemy model for Notes (digitized handwritten notes).

Mirrors the Drizzle schema defined in client/src/db/schema.ts
"""

from typing import Optional
from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class Note(Base, TimestampMixin):
    """
    Digitized note model.
    
    Represents a handwritten note that has been processed 
    and converted to LaTeX format.
    """
    
    __tablename__ = "notes"
    
    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True
    )
    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    original_image_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    extracted_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    latex_content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Note(id={self.id}, title='{self.title[:30]}...')>"

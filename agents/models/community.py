"""
SQLAlchemy models for community feature.
"""

from sqlalchemy import Column, Text, Boolean, ForeignKey, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from models.base import Base


class PostCategory(str, enum.Enum):
    """Category enum for community posts."""
    THEORY = "theory"
    LAB = "lab"
    GENERAL = "general"


class CommunityPost(Base):
    """Community discussion post model."""
    __tablename__ = "community_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    author_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(SQLEnum(PostCategory, name="post_category"), nullable=False, default=PostCategory.GENERAL)
    course_topic = Column(Text, nullable=True)
    is_resolved = Column(Boolean, nullable=False, default=False)
    view_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    author = relationship("User", back_populates="posts", foreign_keys=[author_id])
    comments = relationship("CommunityComment", back_populates="post", cascade="all, delete-orphan")


class CommunityComment(Base):
    """Comment on a community post."""
    __tablename__ = "community_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    post_id = Column(UUID(as_uuid=True), ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)  # NULL for bot
    parent_id = Column(UUID(as_uuid=True), ForeignKey("community_comments.id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    is_bot_reply = Column(Boolean, nullable=False, default=False)
    mentioned_user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    bot_metadata = Column(JSONB, nullable=True)  # Sources, confidence, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    post = relationship("CommunityPost", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])
    mentioned_user = relationship("User", foreign_keys=[mentioned_user_id])
    parent = relationship("CommunityComment", remote_side=[id], backref="replies")


class UserPresence(Base):
    """User online/offline presence tracking."""
    __tablename__ = "user_presence"

    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_online = Column(Boolean, nullable=False, default=False)

    # Relationships
    user = relationship("User", back_populates="presence")

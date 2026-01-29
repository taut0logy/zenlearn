"""
Pydantic schemas for community operations.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from enum import Enum


class PostCategory(str, Enum):
    """Category enum for community posts."""
    THEORY = "theory"
    LAB = "lab"
    GENERAL = "general"


# ============ Request Schemas ============

class PostCreate(BaseModel):
    """Create a new community post."""
    title: str = Field(..., min_length=1, max_length=500, description="Post title")
    content: str = Field(..., min_length=1, max_length=50000, description="Post content (markdown)")
    category: PostCategory = Field(PostCategory.GENERAL, description="Post category")
    course_topic: Optional[str] = Field(None, max_length=200, description="Optional course topic tag")


class PostUpdate(BaseModel):
    """Update an existing post."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1, max_length=50000)
    category: Optional[PostCategory] = None
    course_topic: Optional[str] = Field(None, max_length=200)
    is_resolved: Optional[bool] = None


class CommentCreate(BaseModel):
    """Create a new comment."""
    content: str = Field(..., min_length=1, max_length=10000, description="Comment content")
    parent_id: Optional[UUID] = Field(None, description="Parent comment ID for replies")
    mentioned_user_id: Optional[UUID] = Field(None, description="User being mentioned/replied to")


# ============ Response Schemas ============

class AuthorInfo(BaseModel):
    """Basic author information."""
    id: UUID
    name: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """Comment response with author info."""
    id: UUID
    post_id: UUID
    author: Optional[AuthorInfo] = None
    parent_id: Optional[UUID] = None
    content: str
    is_bot_reply: bool = False
    mentioned_user_id: Optional[UUID] = None
    bot_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    """Post response with author and comment count."""
    id: UUID
    author: AuthorInfo
    title: str
    content: str
    category: PostCategory
    course_topic: Optional[str] = None
    is_resolved: bool = False
    view_count: int = 0
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostDetailResponse(BaseModel):
    """Full post with all comments."""
    id: UUID
    author: AuthorInfo
    title: str
    content: str
    category: PostCategory
    course_topic: Optional[str] = None
    is_resolved: bool = False
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """Paginated list of posts."""
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============ Presence Schemas ============

class PresenceHeartbeat(BaseModel):
    """User presence heartbeat."""
    pass  # Just needs auth, no body required


class PresenceStatus(BaseModel):
    """User presence status."""
    user_id: UUID
    is_online: bool
    last_seen: datetime

    class Config:
        from_attributes = True


class UserPresenceList(BaseModel):
    """List of user presence statuses."""
    users: List[PresenceStatus]


# ============ Bot Response Schemas ============

class BotReplyMetadata(BaseModel):
    """Metadata for bot-generated replies."""
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.0
    course_context: Optional[str] = None
    generated_at: datetime


# Update forward references
CommentResponse.model_rebuild()

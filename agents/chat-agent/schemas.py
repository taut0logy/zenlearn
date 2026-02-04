"""
Pydantic schemas for chat operations.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from enum import Enum


class MessageRole(str, Enum):
    """Message sender role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ============ Request Schemas ============


class ChatCreate(BaseModel):
    """Create a new chat session."""

    title: Optional[str] = Field(
        None, description="Chat title, auto-generated if not provided"
    )


class MessageCreate(BaseModel):
    """Send a message to the chat."""

    content: str = Field(
        ..., min_length=1, max_length=10000, description="Message content"
    )


# ============ Response Schemas ============


class MessageResponse(BaseModel):
    """Message response with metadata."""

    id: UUID
    chat_id: UUID
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Chat session response."""

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ChatDetailResponse(BaseModel):
    """Chat with all messages."""

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ChatListResponse(BaseModel):
    """Paginated list of chats."""

    chats: List[ChatResponse]
    total: int
    page: int
    page_size: int


# ============ Streaming Schemas ============


class StreamEventType(str, Enum):
    """Types of streaming events."""

    START = "start"
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    END = "end"
    ERROR = "error"


class StreamingChunk(BaseModel):
    """Streaming response chunk for SSE."""

    event: StreamEventType
    data: str
    metadata: Optional[Dict[str, Any]] = None


# ============ Agent Internal Schemas ============


class ToolCall(BaseModel):
    """Tool call representation."""

    name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None


class AgentMessage(BaseModel):
    """Internal agent message format."""

    role: MessageRole
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    context: Optional[Dict[str, Any]] = None

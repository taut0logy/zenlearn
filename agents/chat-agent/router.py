"""
FastAPI Router for Chat endpoints.

Provides REST API endpoints for chat operations with
Server-Sent Events (SSE) for streaming responses.
"""

import json
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from middlewares.auth import get_current_user
from utils.logger import logger
from .service import ChatService
from .schemas import (
    ChatCreate, ChatResponse, ChatDetailResponse,
    MessageCreate, MessageResponse, ChatListResponse
)


router = APIRouter(prefix="/chat", tags=["Chat"])


async def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Dependency to get chat service."""
    return ChatService(db)


@router.post("", response_model=ChatResponse)
async def create_chat(
    data: ChatCreate,
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Create a new chat session.
    
    - **title**: Optional title for the chat
    """
    user_id = UUID(user["id"])
    return await service.create_chat(user_id, data.title)


@router.get("", response_model=ChatListResponse)
async def list_chats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    List all chats for the current user.
    
    Supports pagination with page and page_size parameters.
    """
    user_id = UUID(user["id"])
    return await service.list_chats(user_id, page, page_size)


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(
    chat_id: UUID,
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Get a chat with all its messages.
    """
    user_id = UUID(user["id"])
    chat = await service.get_chat(chat_id, user_id)
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return chat


@router.post("/{chat_id}/message")
async def send_message(
    chat_id: UUID,
    data: MessageCreate,
    stream: bool = Query(True, description="Stream the response"),
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to a chat and get a response.
    
    By default, streams the response using Server-Sent Events (SSE).
    Set `stream=false` to get the complete response at once.
    """
    user_id = UUID(user["id"])
    
    if stream:
        # Return SSE stream
        async def event_generator():
            try:
                async for event in service.send_message_stream(
                    chat_id=chat_id,
                    user_id=user_id,
                    content=data.content
                ):
                    event_type = event["event"]
                    event_data = event["data"]
                    
                    yield f"event: {event_type}\ndata: {json.dumps({'content': event_data})}\n\n"
                    
            except HTTPException as e:
                yield f"event: error\ndata: {json.dumps({'error': e.detail})}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Non-streaming response
        response_text = await service.send_message(
            chat_id=chat_id,
            user_id=user_id,
            content=data.content
        )
        
        return {"role": "assistant", "content": response_text}


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: UUID,
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Delete a chat and all its messages.
    """
    user_id = UUID(user["id"])
    deleted = await service.delete_chat(chat_id, user_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {"message": "Chat deleted successfully"}


@router.patch("/{chat_id}/title")
async def update_chat_title(
    chat_id: UUID,
    title: str = Query(..., min_length=1, max_length=255),
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Update the title of a chat.
    """
    user_id = UUID(user["id"])
    chat = await service.update_chat_title(chat_id, user_id, title)
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return chat

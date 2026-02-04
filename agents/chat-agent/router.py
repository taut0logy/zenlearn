"""
FastAPI Router for Chat endpoints.

Provides REST API endpoints for chat operations with
Server-Sent Events (SSE) for streaming responses.
"""

import json
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from middlewares.auth import get_current_user
from utils.logger import logger
from .service import ChatService
from .schemas import (
    ChatCreate,
    ChatResponse,
    ChatDetailResponse,
    MessageCreate,
    MessageResponse,
    ChatListResponse,
    MessageRole,
)


router = APIRouter(prefix="/chat", tags=["Chat"])


async def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Dependency to get chat service."""
    return ChatService(db)


@router.post("", response_model=ChatResponse)
async def create_chat(
    data: ChatCreate,
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
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
    service: ChatService = Depends(get_chat_service),
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
    service: ChatService = Depends(get_chat_service),
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
    chat_id: str,
    data: MessageCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    stream: bool = Query(True, description="Stream the response"),
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Send a message to a chat and get a response.

    By default, streams the response using Server-Sent Events (SSE).
    Set `stream=false` to get the complete response at once.
    """
    user_id = UUID(user["id"])
    target_chat_id = None if chat_id == "new" else UUID(chat_id)

    if stream:
        # Return SSE stream
        async def event_generator():
            try:
                async for event in service.send_message_stream(
                    user_id=user_id,
                    content=data.content,
                    chat_id=target_chat_id,
                    background_tasks=background_tasks,
                ):
                    # Check for client disconnect
                    if await request.is_disconnected():
                        logger.warning("Client disconnected, stopping stream")
                        break
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
                "X-Accel-Buffering": "no",
            },
            background=background_tasks,
        )
    else:
        # Non-streaming response
        response_text = await service.send_message(
            user_id=user_id,
            content=data.content,
            chat_id=target_chat_id,
            background_tasks=background_tasks,
        )

        return {"role": "assistant", "content": response_text}


@router.post("/{chat_id}/message/{message_id}/feedback")
async def record_feedback(
    chat_id: UUID,
    message_id: UUID,
    feedback: str = Query(..., regex="^(like|dislike|none)$"),
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Record user feedback for a message.
    """
    user_id = UUID(user["id"])
    success = await service.record_feedback(chat_id, message_id, user_id, feedback)

    if not success:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"status": "success"}


@router.post("/{chat_id}/regenerate")
async def regenerate_response(
    chat_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Regenerate the last assistant response.
    """
    user_id = UUID(user["id"])

    # 1. Get chat history to find last user message
    chat = await service.get_chat(chat_id, user_id)
    if not chat or not chat.messages:
        raise HTTPException(status_code=400, detail="Cannot regenerate empty chat")

    # Find last user message
    last_user_msg = None
    last_assistant_msg_id = None

    # Messages are in chronological order
    for msg in reversed(chat.messages):
        if msg.role == MessageRole.USER:
            last_user_msg = msg
            break
        elif msg.role == MessageRole.ASSISTANT and not last_assistant_msg_id:
            last_assistant_msg_id = msg.id

    if not last_user_msg:
        raise HTTPException(
            status_code=400, detail="No user message to regenerate from"
        )

    # 2. Delete the last assistant message if it exists
    if last_assistant_msg_id:
        from sqlalchemy import delete
        from models.chat import Message

        await service.db.execute(
            delete(Message).where(Message.id == last_assistant_msg_id)
        )
        await service.db.commit()

    # 3. Trigger a new stream using the last user content
    # We call send_message internally with the same content
    return await send_message(
        chat_id=str(chat_id),
        data=MessageCreate(content=last_user_msg.content),
        request=request,
        background_tasks=background_tasks,
        stream=True,
        user=user,
        service=service,
    )


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: UUID,
    user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
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
    service: ChatService = Depends(get_chat_service),
):
    """
    Update the title of a chat.
    """
    user_id = UUID(user["id"])
    chat = await service.update_chat_title(chat_id, user_id, title)

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return chat

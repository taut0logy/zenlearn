"""
Chat Service - Main orchestration layer.

Handles chat CRUD operations, message processing, and
coordinates between agent, memory, and database.
"""

from typing import List, Optional, AsyncGenerator, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.database import get_db
from models.chat import Chat, Message
from utils.logger import logger
from .agent import get_chat_agent
from .context import ChatContext
from .memory import get_chat_memory
from .tools.semantic_search import get_semantic_search_tool
from .schemas import (
    ChatCreate,
    ChatResponse,
    ChatDetailResponse,
    MessageResponse,
    MessageRole,
    ChatListResponse,
)


class ChatService:
    """
    Service layer for chat operations.

    Coordinates between:
    - Database (chat/message persistence)
    - Agent (response generation)
    - Memory (conversation memory)
    - Semantic search (history indexing)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent = get_chat_agent()
        self.memory = get_chat_memory()
        self.semantic_search = get_semantic_search_tool()

    async def create_chat(
        self, user_id: UUID, title: Optional[str] = None
    ) -> ChatResponse:
        """
        Create a new chat session.

        Args:
            user_id: User ID
            title: Optional chat title

        Returns:
            Created chat response
        """
        chat_id = uuid4()
        now = datetime.now(timezone.utc)

        chat = Chat(
            id=chat_id,
            user_id=user_id,
            title=title or f"New Chat {now.strftime('%Y-%m-%d %H:%M')}",
            created_at=now,
            updated_at=now,
        )

        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)

        logger.info(f"Created chat {chat_id} for user {user_id}")

        return ChatResponse(
            id=chat.id,
            user_id=chat.user_id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            message_count=0,
        )

    async def list_chats(
        self, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> ChatListResponse:
        """
        List all chats for a user.

        Args:
            user_id: User ID
            page: Page number
            page_size: Items per page

        Returns:
            Paginated chat list
        """
        # Count total
        count_query = select(func.count(Chat.id)).where(Chat.user_id == user_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get chats with message count
        offset = (page - 1) * page_size

        query = (
            select(Chat)
            .where(Chat.user_id == user_id)
            .order_by(Chat.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        chats = result.scalars().all()

        # Get message counts
        chat_responses = []
        for chat in chats:
            msg_count_query = select(func.count(Message.id)).where(
                Message.chat_id == chat.id
            )
            msg_count_result = await self.db.execute(msg_count_query)
            msg_count = msg_count_result.scalar() or 0

            chat_responses.append(
                ChatResponse(
                    id=chat.id,
                    user_id=chat.user_id,
                    title=chat.title,
                    created_at=chat.created_at,
                    updated_at=chat.updated_at,
                    message_count=msg_count,
                )
            )

        return ChatListResponse(
            chats=chat_responses, total=total, page=page, page_size=page_size
        )

    async def get_chat(
        self, chat_id: UUID, user_id: UUID
    ) -> Optional[ChatDetailResponse]:
        """
        Get a chat with all messages.

        Args:
            chat_id: Chat ID
            user_id: User ID (for authorization)

        Returns:
            Chat with messages or None if not found
        """
        # Get chat with messages
        query = (
            select(Chat)
            .options(selectinload(Chat.messages))
            .where(Chat.id == chat_id, Chat.user_id == user_id)
        )

        result = await self.db.execute(query)
        chat = result.scalar_one_or_none()

        if not chat:
            return None

        messages = [
            MessageResponse(
                id=msg.id,
                chat_id=msg.chat_id,
                role=MessageRole(msg.role),
                content=msg.content,
                metadata=msg.extra_data,
                created_at=msg.created_at,
            )
            for msg in sorted(chat.messages, key=lambda m: m.created_at)
        ]

        return ChatDetailResponse(
            id=chat.id,
            user_id=chat.user_id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            messages=messages,
        )

    async def send_message(self, chat_id: UUID, user_id: UUID, content: str) -> str:
        """
        Send a message and get a response (non-streaming).

        Args:
            chat_id: Chat ID
            user_id: User ID
            content: Message content

        Returns:
            Assistant response text
        """
        # Verify chat exists and belongs to user
        chat = await self._get_chat_or_raise(chat_id, user_id)

        # Save user message
        user_message = await self._save_message(
            chat_id=chat_id, role="user", content=content
        )

        # Index for semantic search
        self.semantic_search.index_message(
            message_id=str(user_message.id),
            chat_id=str(chat_id),
            user_id=str(user_id),
            role="user",
            content=content,
        )

        # Get chat history
        messages = await self._get_message_history(chat_id)

        # Build context
        context = ChatContext(str(user_id), str(chat_id))
        context_messages = context.build_context(messages, content)

        # Invoke agent
        response_text = await self.agent.invoke(
            user_id=str(user_id),
            chat_id=str(chat_id),
            messages=[
                {"role": m.role.value, "content": m.content}
                for m in context_messages[1:]
            ],  # Skip system
            system_prompt=context.get_system_prompt(),
        )

        # Save assistant message
        assistant_message = await self._save_message(
            chat_id=chat_id, role="assistant", content=response_text
        )

        # Index for semantic search
        self.semantic_search.index_message(
            message_id=str(assistant_message.id),
            chat_id=str(chat_id),
            user_id=str(user_id),
            role="assistant",
            content=response_text,
        )

        # Extract and store memories
        context.extract_and_store_memories(content, response_text)

        # Update chat timestamp
        await self._update_chat_timestamp(chat_id)

        return response_text

    async def send_message_stream(
        self, chat_id: UUID, user_id: UUID, content: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a message and stream the response.

        Args:
            chat_id: Chat ID
            user_id: User ID
            content: Message content

        Yields:
            Stream events
        """
        # Verify chat exists and belongs to user
        chat = await self._get_chat_or_raise(chat_id, user_id)

        # Save user message
        user_message = await self._save_message(
            chat_id=chat_id, role="user", content=content
        )

        # Index for semantic search
        self.semantic_search.index_message(
            message_id=str(user_message.id),
            chat_id=str(chat_id),
            user_id=str(user_id),
            role="user",
            content=content,
        )

        # Get chat history
        messages = await self._get_message_history(chat_id)

        # Build context
        context = ChatContext(str(user_id), str(chat_id))
        context_messages = context.build_context(messages, content)

        # Stream agent response
        full_response = ""

        async for event in self.agent.stream(
            user_id=str(user_id),
            chat_id=str(chat_id),
            messages=[
                {"role": m.role.value, "content": m.content}
                for m in context_messages[1:]
            ],
            system_prompt=context.get_system_prompt(),
        ):
            yield event

            if event["event"] == "token":
                full_response += event["data"]

        # Save assistant message
        if full_response:
            assistant_message = await self._save_message(
                chat_id=chat_id, role="assistant", content=full_response
            )

            # Index for semantic search
            self.semantic_search.index_message(
                message_id=str(assistant_message.id),
                chat_id=str(chat_id),
                user_id=str(user_id),
                role="assistant",
                content=full_response,
            )

            # Extract and store memories
            context.extract_and_store_memories(content, full_response)

        # Update chat timestamp
        await self._update_chat_timestamp(chat_id)

        # Auto-generate title for new chats after first message
        if chat.title.startswith("New Chat"):
            await self._auto_generate_title(chat_id, content, full_response)

    async def delete_chat(self, chat_id: UUID, user_id: UUID) -> bool:
        """
        Delete a chat and all its messages.

        Args:
            chat_id: Chat ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        # Verify ownership
        chat = await self._get_chat_or_raise(chat_id, user_id)

        if not chat:
            return False

        # Delete from semantic search index
        self.semantic_search.delete_chat_messages(str(chat_id))

        # Delete memories
        self.memory.clear_chat_memories(str(chat_id))

        # Delete chat (messages cascade)
        await self.db.execute(delete(Chat).where(Chat.id == chat_id))
        await self.db.commit()

        logger.info(f"Deleted chat {chat_id}")
        return True

    async def update_chat_title(
        self, chat_id: UUID, user_id: UUID, title: str
    ) -> Optional[ChatResponse]:
        """
        Update chat title.

        Args:
            chat_id: Chat ID
            user_id: User ID
            title: New title

        Returns:
            Updated chat or None
        """
        chat = await self._get_chat_or_raise(chat_id, user_id)

        if not chat:
            return None

        await self.db.execute(
            update(Chat)
            .where(Chat.id == chat_id)
            .values(title=title, updated_at=datetime.now(timezone.utc))
        )
        await self.db.commit()

        return await self.get_chat(chat_id, user_id)

    # ============ Private Methods ============

    async def _get_chat_or_raise(self, chat_id: UUID, user_id: UUID) -> Optional[Chat]:
        """Get chat or raise if not found/unauthorized."""
        query = select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        result = await self.db.execute(query)
        chat = result.scalar_one_or_none()

        if not chat:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Chat not found")

        return chat

    async def _save_message(
        self, chat_id: UUID, role: str, content: str, metadata: Optional[dict] = None
    ) -> Message:
        """Save a message to the database."""
        message = Message(
            id=uuid4(),
            chat_id=chat_id,
            role=role,
            content=content,
            metadata=metadata,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def _get_message_history(self, chat_id: UUID, limit: int = 50) -> List[dict]:
        """Get message history for a chat."""
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # Reverse to chronological order and convert to dicts
        return [
            {"role": msg.role, "content": msg.content} for msg in reversed(messages)
        ]

    async def _update_chat_timestamp(self, chat_id: UUID) -> None:
        """Update chat's updated_at timestamp."""
        await self.db.execute(
            update(Chat)
            .where(Chat.id == chat_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self.db.commit()

    async def _auto_generate_title(
        self, chat_id: UUID, user_message: str, assistant_response: str
    ) -> None:
        """Auto-generate a chat title based on the conversation."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from config.settings import settings

            # Use a fast model for title generation
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,
            )

            # Create a simple prompt for title generation
            prompt = f"""Generate a short, descriptive title (3-6 words) for this conversation.
            
User: {user_message[:200]}
Assistant: {assistant_response[:200]}

Rules:
- Maximum 6 words
- No quotes or special characters
- Descriptive and relevant
- Don't start with "Question about" or similar

Title:"""

            response = await llm.ainvoke(prompt)
            title = response.content.strip()

            # Clean up the title
            title = title.replace('"', "").replace("'", "").strip()
            if len(title) > 60:
                title = title[:57] + "..."

            # Update the chat title
            await self.db.execute(
                update(Chat)
                .where(Chat.id == chat_id)
                .values(title=title, updated_at=datetime.now(timezone.utc))
            )
            await self.db.commit()

            logger.info(f"Auto-generated title for chat {chat_id}: {title}")

        except Exception as e:
            logger.warning(f"Failed to auto-generate title: {e}")
            # Don't raise - title generation is non-critical


async def get_chat_service(db: AsyncSession) -> ChatService:
    """Dependency to get chat service."""
    return ChatService(db)

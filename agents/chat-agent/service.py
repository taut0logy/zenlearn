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

from config.database import get_db, get_db_context
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

    async def send_message(
        self,
        user_id: UUID,
        content: str,
        chat_id: Optional[UUID] = None,
        background_tasks: Optional[any] = None,
    ) -> str:
        """
        Send a message and get a response (non-streaming).

        Args:
            chat_id: Chat ID
            user_id: User ID
            content: Message content
            background_tasks: FastAPI BackgroundTasks for offloading operations
        """
        from fastapi import BackgroundTasks

        # 1. Handle Chat Session (Existing or New)
        is_new_chat = False
        if chat_id is None:
            title = content[:50] + "..." if len(content) > 50 else content
            chat = await self.create_chat(user_id, title)
            chat_id = chat.id
            is_new_chat = True
        else:
            # Verify chat exists and belongs to user
            chat = await self._get_chat_or_raise(chat_id, user_id)

        # Build context
        context = ChatContext(str(user_id), str(chat_id))

        # Save user message
        user_message = await self._save_message(
            chat_id=chat_id, role="user", content=content
        )

        # Offload Indexing for semantic search
        if background_tasks and isinstance(background_tasks, BackgroundTasks):
            background_tasks.add_task(
                self.semantic_search.index_message,
                message_id=str(user_message.id),
                chat_id=str(chat_id),
                user_id=str(user_id),
                role="user",
                content=content,
            )
        else:
            self.semantic_search.index_message(
                message_id=str(user_message.id),
                chat_id=str(chat_id),
                user_id=str(user_id),
                role="user",
                content=content,
            )

        # Get chat history (from Redis or DB)
        messages = await self._get_message_history(chat_id)

        # Now build context (retrieves memories)
        context_messages = await context.build_context(messages, content)

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

        # Offload Assistant Indexing & Memory Extraction
        if background_tasks and hasattr(background_tasks, "add_task"):
            background_tasks.add_task(
                self.semantic_search.index_message,
                message_id=str(assistant_message.id),
                chat_id=str(chat_id),
                user_id=str(user_id),
                role="assistant",
                content=response_text,
            )
            background_tasks.add_task(
                context.extract_and_store_memories, content, response_text
            )
            background_tasks.add_task(self._update_chat_timestamp, chat_id)
            if is_new_chat:
                background_tasks.add_task(
                    self._auto_generate_title, chat_id, content, response_text
                )
        else:
            self.semantic_search.index_message(
                message_id=str(assistant_message.id),
                chat_id=str(chat_id),
                user_id=str(user_id),
                role="assistant",
                content=response_text,
            )
            context.extract_and_store_memories(content, response_text)
            await self._update_chat_timestamp(chat_id)
            if is_new_chat:
                await self._auto_generate_title(chat_id, content, response_text)

        return response_text

    async def send_message_stream(
        self,
        user_id: UUID,
        content: str,
        chat_id: Optional[UUID] = None,
        background_tasks: Optional[any] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a message and stream the response.
        """
        from fastapi import BackgroundTasks

        # 1. Handle Chat Session (Existing or New)
        is_new_chat = False
        if chat_id is None:
            # Create a placeholder title, will be auto-updated in background
            title = content[:50] + "..." if len(content) > 50 else content
            chat = await self.create_chat(user_id, title)
            chat_id = chat.id
            is_new_chat = True
        else:
            # Verify chat exists and belongs to user
            chat = await self._get_chat_or_raise(chat_id, user_id)

        # Build context
        context = ChatContext(str(user_id), str(chat_id))

        if is_new_chat:
            yield {"event": "chat_created", "data": str(chat_id)}

        # Save user message
        user_message = await self._save_message(
            chat_id=chat_id, role="user", content=content
        )

        # Offload User Indexing
        if background_tasks and hasattr(background_tasks, "add_task"):
            background_tasks.add_task(
                self.semantic_search.index_message,
                message_id=str(user_message.id),
                chat_id=str(chat_id),
                user_id=str(user_id),
                role="user",
                content=content,
            )
        else:
            self.semantic_search.index_message(
                message_id=str(user_message.id),
                chat_id=str(chat_id),
                user_id=str(user_id),
                role="user",
                content=content,
            )

        # Get chat history (Redis/DB)
        messages = await self._get_message_history(chat_id)

        # Now build context (fetches memories asynchronously)
        context_messages = await context.build_context(messages, content)

        # Stream agent response
        full_response = ""

        # Using the agent's stream method
        # Note: We can't easily offload starting the stream, but we offload post-processing
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

            logger.info(
                f"Finished streaming. Background tasks type: {type(background_tasks)}"
            )

            # Offload Assistant Indexing, Memory, Timestamp, Title
            if background_tasks and hasattr(background_tasks, "add_task"):
                background_tasks.add_task(
                    self.semantic_search.index_message,
                    message_id=str(assistant_message.id),
                    chat_id=str(chat_id),
                    user_id=str(user_id),
                    role="assistant",
                    content=full_response,
                )
                background_tasks.add_task(
                    context.extract_and_store_memories, content, full_response
                )
                background_tasks.add_task(self._update_chat_timestamp, chat_id)

                if is_new_chat:
                    background_tasks.add_task(
                        self._auto_generate_title, chat_id, content, full_response
                    )
            else:
                self.semantic_search.index_message(
                    message_id=str(assistant_message.id),
                    chat_id=str(chat_id),
                    user_id=str(user_id),
                    role="assistant",
                    content=full_response,
                )
                context.extract_and_store_memories(content, full_response)
                await self._update_chat_timestamp(chat_id)
                if is_new_chat:
                    await self._auto_generate_title(chat_id, content, full_response)

    async def delete_chat(self, chat_id: UUID, user_id: UUID) -> bool:
        """
        Delete a chat and all its messages.
        """
        # Verify ownership
        chat = await self._get_chat_or_raise(chat_id, user_id)

        if not chat:
            return False

        # Delete from semantic search index
        self.semantic_search.delete_chat_messages(str(chat_id))

        # Delete memories
        self.memory.clear_chat_memories(str(chat_id), str(user_id))

        # Clear Redis Cache
        from utils.redis_client import redis_client

        if redis_client.redis:
            await redis_client.redis.delete(f"chat:{chat_id}:history")

        # Delete chat (messages cascade)
        await self.db.execute(delete(Chat).where(Chat.id == chat_id))
        await self.db.commit()

        logger.info(f"Deleted chat {chat_id}")
        return True

    # ... update_chat_title remains same ...

    async def update_chat_title(
        self, chat_id: UUID, user_id: UUID, title: str
    ) -> Optional[ChatResponse]:
        """Update chat title."""
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

    async def record_feedback(
        self, chat_id: UUID, message_id: UUID, user_id: UUID, feedback: str
    ) -> bool:
        """
        Record user feedback (e.g., 'like', 'dislike') for a message.
        """
        # Verify chat/message ownership
        await self._get_chat_or_raise(chat_id, user_id)

        # Update message metadata
        query = select(Message).where(
            Message.id == message_id, Message.chat_id == chat_id
        )
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            return False

        current_metadata = message.extra_data or {}
        current_metadata["user_feedback"] = feedback
        current_metadata["feedback_at"] = datetime.now(timezone.utc).isoformat()

        message.extra_data = current_metadata
        await self.db.commit()

        logger.info(f"Recorded {feedback} feedback for message {message_id}")
        return True

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
        """
        Save a message to the database AND Redis cache.
        """
        # 1. Save to Postgres
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

        # 2. Update Redis Cache (Async/Fire-and-forget style)
        from utils.redis_client import redis_client

        try:
            # Make sure we connect if not connected?
            # Ideally connection pool is managed at app startup lifecycle.
            # We assume app startup called redis_client.connect()

            msg_dict = {
                "role": role,
                "content": content,
                # "created_at": message.created_at.isoformat()
            }
            await redis_client.add_message_to_history(str(chat_id), msg_dict, limit=100)
        except Exception as e:
            logger.warning(f"Failed to update Redis cache: {e}")

        return message

    async def _get_message_history(self, chat_id: UUID, limit: int = 100) -> List[dict]:
        """
        Get message history for a chat.
        Strategy: Redis Cache -> DB -> Set Cache
        """
        from utils.redis_client import redis_client

        # 1. Try Redis
        cached_messages = await redis_client.get_chat_history(str(chat_id))
        if cached_messages:
            # Redis stores them in chronological order (oldest -> newest) for display/context?
            # Our prompt builder expects reversed (newest -> oldest)?
            # service.py original _get_message_history reversed them at the end.

            # Redis lrange(0, -1) returns [msg1, msg2, msg3] (chronological if we pushed right)
            # We want to return [msg3, msg2, msg1] (reversed) to match original behavior?
            # Original: return [{"role": ...}] for msg in reversed(messages)

            # If Redis stores chronological:

            logger.info(f"Using cached messages for chat {chat_id}")
            return list(reversed(cached_messages))

        # 2. Fallback to DB
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()  # These are Newest -> Oldest (DESC)

        # 3. Populate Redis (Needs Chronological for RPUSH)
        # messages is DESC (Newest First). Reverse it to ASC (Oldest First) for Redis list
        chronological_msgs = [
            {"role": msg.role, "content": msg.content} for msg in reversed(messages)
        ]

        if chronological_msgs:
            await redis_client.set_chat_history(
                str(chat_id), chronological_msgs, limit=limit
            )

        # 4. Return format (Original service returned Text-dicts in Newest-First order? Wait.)
        # Original: return [dict(msg) for msg in reversed(messages)]
        # Original Query was DESC.
        # reversed(DESC) = ASC (Chronological).
        # Actually, let's look at the ORIGINAL return logic:
        # return [{"role": msg.role, "content": msg.content} for msg in reversed(messages)]
        # If query was DESC (Newest first), reversed makes it ASC (Oldest first).

        # So Context builder expects CHRONOLOGICAL (Oldest -> Newest)?
        # Let's check ChatContext.build_context:
        # "for msg in reversed(messages):" -> it takes the list and REVERSES it again?
        # If input is [Old, Med, New] -> reversed -> [New, Med, Old].
        # It processes newest first to fill context window.

        # So _get_message_history must return CHRONOLOGICAL order.
        logger.info(f"Returning DB retrieved chronological messages for chat {chat_id}")
        return chronological_msgs

    async def _update_chat_timestamp(self, chat_id: UUID) -> None:
        """Update chat's updated_at timestamp."""
        async with get_db_context() as db:
            await db.execute(
                update(Chat)
                .where(Chat.id == chat_id)
                .values(updated_at=datetime.now(timezone.utc))
            )
            # Commit is handled by get_db_context

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
            async with get_db_context() as db:
                await db.execute(
                    update(Chat)
                    .where(Chat.id == chat_id)
                    .values(title=title, updated_at=datetime.now(timezone.utc))
                )
                # Commit handled by context

            logger.info(f"Auto-generated title for chat {chat_id}: {title}")

        except Exception as e:
            logger.warning(f"Failed to auto-generate title: {e}")
            # Don't raise - title generation is non-critical


async def get_chat_service(db: AsyncSession) -> ChatService:
    """Dependency to get chat service."""
    return ChatService(db)

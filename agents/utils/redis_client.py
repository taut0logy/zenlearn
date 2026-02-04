"""
Async Redis Client for ZenLearn.

Handles connection pooling and chat history caching operations.
"""

from typing import List, Optional, Dict
import json
from redis import asyncio as redis
from config.settings import settings
from utils.logger import logger


class RedisClient:
    """Async Redis client wrapper."""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.ttl = settings.CACHE_TTL

    async def connect(self):
        """Establish Redis connection pool."""
        if not self.redis:
            try:
                self.redis = redis.from_url(
                    settings.REDIS_URL, encoding="utf-8", decode_responses=True
                )
                await self.redis.ping()
                logger.info("Redis connected successfully.")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis = None

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def get_chat_history(self, chat_id: str) -> List[Dict]:
        """Get cached chat history."""
        if not self.redis:
            return []

        try:
            # Get list from Redis
            key = f"chat:{chat_id}:history"
            data = await self.redis.lrange(key, 0, -1)

            # Parse JSON strings back to dicts
            return [json.loads(msg) for msg in data]
        except Exception as e:
            logger.error(f"Redis get_chat_history error: {e}")
            return []

    async def add_message_to_history(
        self, chat_id: str, message: Dict, limit: int = 100
    ):
        """
        Add a message to the chat history cache.
        Pushes to the right (end) and trims from left (start) to maintain limit.
        """
        if not self.redis:
            return

        try:
            key = f"chat:{chat_id}:history"

            # Serialize
            msg_str = json.dumps(message)

            async with self.redis.pipeline() as pipe:
                pipe.rpush(key, msg_str)
                pipe.ltrim(key, -limit, -1)  # Keep last N elements
                pipe.expire(key, self.ttl)
                await pipe.execute()

        except Exception as e:
            logger.error(f"Redis add_message_to_history error: {e}")

    async def set_chat_history(
        self, chat_id: str, messages: List[Dict], limit: int = 100
    ):
        """Overwrite cache with full history (e.g. after DB fetch)."""
        if not self.redis:
            return

        try:
            key = f"chat:{chat_id}:history"

            # Prepare all messages
            # Ensure we respect limit (take last N)
            messages_to_cache = messages[-limit:] if len(messages) > limit else messages
            encoded_msgs = [json.dumps(m) for m in messages_to_cache]

            if not encoded_msgs:
                return

            async with self.redis.pipeline() as pipe:
                pipe.delete(key)
                pipe.rpush(key, *encoded_msgs)
                pipe.expire(key, self.ttl)
                await pipe.execute()

        except Exception as e:
            logger.error(f"Redis set_chat_history error: {e}")


# Singleton
redis_client = RedisClient()

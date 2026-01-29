from slowapi import Limiter
from slowapi.util import get_remote_address

from config.settings import settings
from utils.logger import logger


def _get_storage():
    """Get appropriate storage backend based on environment."""
    if settings.is_production and settings.RATE_LIMIT_ENABLED:
        try:
            from redis import Redis

            redis_client = Redis.from_url(settings.REDIS_URL)
            redis_client.ping()

            logger.info(
                f"Rate limiter using Redis: {settings.REDIS_URL.split('@')[-1]}"
            )

            return settings.REDIS_URL
        except Exception as e:
            logger.warning(f"Redis unavailable, falling back to memory storage: {e}")
            return None
    else:
        logger.info("Rate limiter using in-memory storage (development mode)")
        return None

_storage_uri = _get_storage()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
    storage_uri=_storage_uri,
    enabled=settings.RATE_LIMIT_ENABLED,
)

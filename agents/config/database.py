from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from config.settings import settings
from utils.logger import logger

engine = create_async_engine(
    settings.DB_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=1800,  # Recycle connections after 30 minutes
    connect_args={"statement_cache_size": 0},
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Usage in FastAPI routes:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of request context.

    Usage:
        async with get_db_context() as db:
            result = await db.execute(...)
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> str:
    """
    Check database connectivity for health checks.

    Returns:
        str with connection status and details
    """
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            return "connected"
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return "disconnected"


async def init_db() -> None:
    """Initialize database connection on startup."""
    logger.info("Initializing database connection...")
    try:
        status = await check_db_connection()
        if status == "connected":
            logger.info(f"Database connected: {status}")
        else:
            logger.warning(f"Database not available: {status}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


async def close_db() -> None:
    """Close database connection on shutdown."""
    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Database connection closed")

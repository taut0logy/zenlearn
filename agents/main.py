import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config.database import check_db_connection, close_db, init_db
from config.limiter import limiter
from config.settings import settings
from utils.logger import logger, request_id_ctx
from api.test import router as test_router
from cms_agent.router import router as cms_router
from fastapi.staticfiles import StaticFiles
import os
from fastapi.staticfiles import StaticFiles
import os

# Import chat agent router
import sys
sys.path.insert(0, '.')
try:
    from importlib import import_module
    chat_agent_router = import_module('chat-agent.router')
    chat_router = chat_agent_router.router
except ImportError as e:
    print(f"Warning: Could not import chat-agent router: {e}")
    chat_router = None

# Import chat agent router
import sys
sys.path.insert(0, '.')
try:
    from importlib import import_module
    chat_agent_router = import_module('chat-agent.router')
    chat_router = chat_agent_router.router
except ImportError as e:
    print(f"Warning: Could not import chat-agent router: {e}")
    chat_router = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready Python API Server",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Request ID middleware for tracing
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add unique request ID for tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_ctx.set(request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    request_id = request_id_ctx.get()
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"request_id": request_id, "path": request.url.path},
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
        },
    )


# Include routers with prefix
app.include_router(test_router, prefix=settings.API_PREFIX)

app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(cms_router, prefix=settings.API_PREFIX)

# Mount contents directory
content_dir = os.path.join(settings.BASE_DIR, "contents")
os.makedirs(content_dir, exist_ok=True)
app.mount("/contents", StaticFiles(directory=content_dir), name="contents")


@app.get("/")
async def root(request: Request):
    """Root endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "docs_url": str(request.url_for("swagger_ui_html"))
            if settings.DEBUG
            else None,
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint with database status."""
    db_status = await check_db_connection()

    if db_status == "connected":
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "database": db_status},
        )

    return JSONResponse(
        status_code=500,
        content={"detail": "Database connection failed.", "database": db_status},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )

"""
API endpoints for Notes digitization.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from config.database import get_db
from middlewares.auth import get_current_user
from utils.logger import logger

# Import from notes_agent module
from notes_agent.schemas import DigitizeRequest, DigitizeResponse
from notes_agent.agent import get_notes_agent

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/digitize", response_model=DigitizeResponse)
async def digitize_note(
    request: DigitizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Digitize a handwritten note image.
    
    Accepts a base64 encoded image and returns:
    - Extracted text
    - LaTeX formatted content
    - Structured content blocks
    """
    try:
        logger.info(f"Digitize request from user {current_user.get('id', 'unknown')}")
        
        agent = get_notes_agent()
        
        # Detect MIME type from base64 header if present
        mime_type = "image/png"
        if request.image_base64.startswith("data:"):
            # Extract MIME type from data URL
            header_end = request.image_base64.find(",")
            if header_end > 0:
                header = request.image_base64[:header_end]
                if "image/jpeg" in header:
                    mime_type = "image/jpeg"
                elif "image/png" in header:
                    mime_type = "image/png"
                elif "image/webp" in header:
                    mime_type = "image/webp"
                # Remove data URL prefix
                request.image_base64 = request.image_base64[header_end + 1:]
        
        result = await agent.digitize(request, mime_type)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Digitize endpoint error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def notes_health():
    """Health check for notes service."""
    return {"status": "ok", "service": "notes-digitizer"}

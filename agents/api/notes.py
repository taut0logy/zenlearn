"""
API endpoints for Notes digitization.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from config.database import get_db
from middlewares.auth import get_current_user
from utils.logger import logger

# Import from notes_agent module
from notes_agent.schemas import DigitizeRequest, DigitizeResponse, BatchDigitizeRequest
from notes_agent.agent import get_notes_agent

router = APIRouter(prefix="/notes", tags=["notes"])


def _extract_mime_type(base64_data: str) -> tuple:
    """Extract MIME type and clean base64 data."""
    mime_type = "image/png"
    clean_data = base64_data

    if base64_data.startswith("data:"):
        header_end = base64_data.find(",")
        if header_end > 0:
            header = base64_data[:header_end]
            if "image/jpeg" in header:
                mime_type = "image/jpeg"
            elif "image/png" in header:
                mime_type = "image/png"
            elif "image/webp" in header:
                mime_type = "image/webp"
            clean_data = base64_data[header_end + 1 :]

    return mime_type, clean_data


@router.post("/digitize", response_model=DigitizeResponse)
async def digitize_note(
    request: DigitizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Digitize a single handwritten note image.

    Accepts a base64 encoded image and returns:
    - Extracted text
    - LaTeX formatted content
    - Structured content blocks
    """
    try:
        logger.info(f"Digitize request from user {current_user.get('id', 'unknown')}")

        agent = get_notes_agent()

        # Extract MIME type and clean base64 data
        mime_type, clean_data = _extract_mime_type(request.image_base64)
        request.image_base64 = clean_data

        result = await agent.digitize(request, mime_type)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Digitize endpoint error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/digitize/batch", response_model=DigitizeResponse)
async def batch_digitize_notes(
    request: BatchDigitizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Digitize multiple handwritten note images (up to 10).

    The AI will analyze all images and determine if they are related.
    If related, content will be merged into a single coherent document.

    Accepts:
    - images: List of base64 encoded images (max 10)
    - title: Optional title for the notes
    - merge_related: Whether to merge related content (default: true)

    Returns:
    - Merged/organized LaTeX content
    - Structured content blocks with source_image index
    """
    try:
        logger.info(
            f"Batch digitize request from user {current_user.get('id', 'unknown')} "
            f"with {len(request.images)} images"
        )

        agent = get_notes_agent()

        # Extract MIME types and clean base64 data for each image
        mime_types = []
        clean_images = []
        for img in request.images:
            mime_type, clean_data = _extract_mime_type(img)
            mime_types.append(mime_type)
            clean_images.append(clean_data)

        request.images = clean_images

        result = await agent.batch_digitize(request, mime_types)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch digitize endpoint error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def notes_health():
    """Health check for notes service."""
    return {"status": "ok", "service": "notes-digitizer"}

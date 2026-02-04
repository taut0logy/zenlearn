"""
Notes Agent - Main agent for handwritten notes digitization.

Uses Gemini Vision to extract text from images and generates LaTeX output.
"""

import uuid
from typing import Optional, List
from utils.logger import logger
from .vision import get_vision_processor
from .latex_generator import get_latex_generator
from .schemas import (
    DigitizeRequest,
    DigitizeResponse,
    ExtractedBlock,
    BatchDigitizeRequest,
)


class NotesAgent:
    """
    Agent for processing handwritten notes.

    Pipeline:
    1. Receive image(s) (base64)
    2. Extract text using Gemini Vision
    3. Generate LaTeX from extracted blocks
    4. Return structured response
    """

    def __init__(self):
        self.vision = get_vision_processor()
        self.latex = get_latex_generator()

    async def digitize(
        self, request: DigitizeRequest, mime_type: str = "image/png"
    ) -> DigitizeResponse:
        """
        Digitize a single handwritten note image.
        """
        note_id = str(uuid.uuid4())

        try:
            logger.info(f"Starting digitization for note {note_id}")

            extraction_result = await self.vision.extract_from_image(
                request.image_base64, mime_type
            )

            if "error" in extraction_result:
                return DigitizeResponse(
                    id=note_id,
                    title=request.title or "Failed Extraction",
                    extracted_text="",
                    latex_content="",
                    blocks=[],
                    success=False,
                    error=extraction_result["error"],
                )

            title = request.title or extraction_result.get("title", "Untitled Note")
            blocks = extraction_result.get("blocks", [])
            full_text = extraction_result.get("full_text", "")

            latex_fragment = self.latex.generate_latex_fragment(blocks, full_text)

            extracted_blocks = [
                ExtractedBlock(
                    type=block.get("type", "paragraph"),
                    content=block.get("content", ""),
                    confidence=block.get("confidence", 0.0),
                    source_image=block.get("source_image", 0),
                )
                for block in blocks
            ]

            logger.info(
                f"Digitization complete for note {note_id}: {len(blocks)} blocks extracted"
            )

            return DigitizeResponse(
                id=note_id,
                title=title,
                extracted_text=full_text,
                latex_content=latex_fragment,
                blocks=extracted_blocks,
                success=True,
                image_count=1,
                merged=False,
            )

        except Exception as e:
            logger.error(f"Digitization error: {type(e).__name__}: {e}")
            return DigitizeResponse(
                id=note_id,
                title=request.title or "Error",
                extracted_text="",
                latex_content="",
                blocks=[],
                success=False,
                error=str(e),
            )

    async def batch_digitize(
        self, request: BatchDigitizeRequest, mime_types: List[str] = None
    ) -> DigitizeResponse:
        """
        Digitize multiple handwritten note images.

        The AI determines whether to merge related content into
        a single coherent document or keep them separate.

        Args:
            request: Contains list of base64 images and options
            mime_types: List of MIME types for each image

        Returns:
            DigitizeResponse with merged/organized content
        """
        note_id = str(uuid.uuid4())

        try:
            logger.info(f"Starting batch digitization for {len(request.images)} images")

            # Process all images together with AI merging
            extraction_result = await self.vision.extract_from_multiple_images(
                request.images, mime_types, request.merge_related
            )

            if "error" in extraction_result and extraction_result.get("error"):
                return DigitizeResponse(
                    id=note_id,
                    title=request.title or "Failed Extraction",
                    extracted_text="",
                    latex_content="",
                    blocks=[],
                    success=False,
                    error=extraction_result["error"],
                    image_count=len(request.images),
                    merged=False,
                )

            title = request.title or extraction_result.get("title", "Untitled Notes")
            blocks = extraction_result.get("blocks", [])
            full_text = extraction_result.get("full_text", "")
            is_merged = extraction_result.get(
                "merged", extraction_result.get("is_related", True)
            )

            # Generate LaTeX
            latex_fragment = self.latex.generate_latex_fragment(blocks, full_text)

            # Convert blocks to schema format
            extracted_blocks = [
                ExtractedBlock(
                    type=block.get("type", "paragraph"),
                    content=block.get("content", ""),
                    confidence=block.get("confidence", 0.0),
                    source_image=block.get("source_image", 0),
                )
                for block in blocks
            ]

            logger.info(
                f"Batch digitization complete: {len(blocks)} blocks from "
                f"{len(request.images)} images, merged={is_merged}"
            )

            return DigitizeResponse(
                id=note_id,
                title=title,
                extracted_text=full_text,
                latex_content=latex_fragment,
                blocks=extracted_blocks,
                success=True,
                image_count=len(request.images),
                merged=is_merged,
            )

        except Exception as e:
            logger.error(f"Batch digitization error: {type(e).__name__}: {e}")
            return DigitizeResponse(
                id=note_id,
                title=request.title or "Error",
                extracted_text="",
                latex_content="",
                blocks=[],
                success=False,
                error=str(e),
                image_count=len(request.images),
                merged=False,
            )


# Singleton instance
_notes_agent: Optional[NotesAgent] = None


def get_notes_agent() -> NotesAgent:
    """Get or create the notes agent instance."""
    global _notes_agent
    if _notes_agent is None:
        _notes_agent = NotesAgent()
    return _notes_agent

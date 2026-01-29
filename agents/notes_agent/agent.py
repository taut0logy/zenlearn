"""
Notes Agent - Main agent for handwritten notes digitization.

Uses Gemini Vision to extract text from images and generates LaTeX output.
"""

import uuid
from typing import Optional, Dict, Any
from utils.logger import logger
from .vision import get_vision_processor
from .latex_generator import get_latex_generator
from .schemas import DigitizeRequest, DigitizeResponse, ExtractedBlock


class NotesAgent:
    """
    Agent for processing handwritten notes.
    
    Pipeline:
    1. Receive image (base64)
    2. Extract text using Gemini Vision
    3. Generate LaTeX from extracted blocks
    4. Return structured response
    """
    
    def __init__(self):
        self.vision = get_vision_processor()
        self.latex = get_latex_generator()
    
    async def digitize(
        self, 
        request: DigitizeRequest,
        mime_type: str = "image/png"
    ) -> DigitizeResponse:
        """
        Digitize a handwritten note image.
        
        Args:
            request: Contains base64 image and optional title
            mime_type: Image MIME type
            
        Returns:
            DigitizeResponse with extracted text and LaTeX
        """
        note_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting digitization for note {note_id}")
            
            # Step 1: Extract text from image using Gemini Vision
            extraction_result = await self.vision.extract_from_image(
                request.image_base64,
                mime_type
            )
            
            if "error" in extraction_result:
                return DigitizeResponse(
                    id=note_id,
                    title=request.title or "Failed Extraction",
                    extracted_text="",
                    latex_content="",
                    blocks=[],
                    success=False,
                    error=extraction_result["error"]
                )
            
            # Get extracted data
            title = request.title or extraction_result.get("title", "Untitled Note")
            blocks = extraction_result.get("blocks", [])
            full_text = extraction_result.get("full_text", "")
            
            # Step 2: Generate LaTeX from extracted blocks
            latex_content = self.latex.generate_latex(title, blocks, full_text)
            latex_fragment = self.latex.generate_latex_fragment(blocks, full_text)
            
            # Convert blocks to schema format
            extracted_blocks = [
                ExtractedBlock(
                    type=block.get("type", "paragraph"),
                    content=block.get("content", ""),
                    confidence=block.get("confidence", 0.0)
                )
                for block in blocks
            ]
            
            logger.info(f"Digitization complete for note {note_id}: {len(blocks)} blocks extracted")
            
            # Debug output
            print(f"\n{'='*50}")
            print("NOTES AGENT RESULT:")
            print(f"{'='*50}")
            print(f"Title: {title}")
            print(f"Blocks: {len(blocks)}")
            print(f"LaTeX Preview:\n{latex_fragment[:500]}...")
            print(f"{'='*50}\n")
            
            return DigitizeResponse(
                id=note_id,
                title=title,
                extracted_text=full_text,
                latex_content=latex_fragment,  # Use fragment for frontend rendering
                blocks=extracted_blocks,
                success=True
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
                error=str(e)
            )


# Singleton instance
_notes_agent: Optional[NotesAgent] = None


def get_notes_agent() -> NotesAgent:
    """Get or create the notes agent instance."""
    global _notes_agent
    if _notes_agent is None:
        _notes_agent = NotesAgent()
    return _notes_agent

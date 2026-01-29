"""
Pydantic schemas for the Notes Agent API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class DigitizeRequest(BaseModel):
    """Request to digitize a handwritten note image."""
    image_base64: str = Field(..., description="Base64 encoded image data")
    title: Optional[str] = Field(None, description="Optional title for the note")
    

class ExtractedBlock(BaseModel):
    """A block of extracted content from the image."""
    type: str = Field(..., description="Type: heading, paragraph, equation, list, diagram")
    content: str = Field(..., description="Extracted text content")
    confidence: float = Field(0.0, description="Confidence score 0-1")


class DigitizeResponse(BaseModel):
    """Response from digitization."""
    id: str = Field(..., description="Note ID")
    title: str = Field(..., description="Note title")
    extracted_text: str = Field(..., description="Plain text extraction")
    latex_content: str = Field(..., description="LaTeX formatted content")
    blocks: List[ExtractedBlock] = Field(default_factory=list, description="Structured blocks")
    success: bool = Field(True)
    error: Optional[str] = None


class Note(BaseModel):
    """A stored digitized note."""
    id: UUID
    user_id: UUID
    title: str
    original_image_url: Optional[str] = None
    extracted_text: str
    latex_content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """List of notes."""
    notes: List[Note]
    total: int

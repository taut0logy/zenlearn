"""
Pydantic schemas for the Notes Agent API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class DigitizeRequest(BaseModel):
    """Request to digitize a handwritten note image."""

    image_base64: str = Field(..., description="Base64 encoded image data")
    title: Optional[str] = Field(None, description="Optional title for the note")


class BatchDigitizeRequest(BaseModel):
    """Request to digitize multiple handwritten note images."""

    images: List[str] = Field(..., description="List of base64 encoded images (max 10)")
    title: Optional[str] = Field(None, description="Optional title for the notes")
    merge_related: bool = Field(
        True, description="AI decides whether to merge related content"
    )

    @field_validator("images")
    @classmethod
    def validate_images(cls, v):
        if len(v) > 10:
            raise ValueError("Maximum 10 images allowed per request")
        if len(v) == 0:
            raise ValueError("At least one image is required")
        return v


class ExtractedBlock(BaseModel):
    """A block of extracted content from the image."""

    type: str = Field(
        ..., description="Type: heading, paragraph, equation, list, diagram"
    )
    content: str = Field(..., description="Extracted text content")
    confidence: float = Field(0.0, description="Confidence score 0-1")
    source_image: int = Field(0, description="Index of source image (0-based)")


class ImageResult(BaseModel):
    """Result from processing a single image."""

    image_index: int = Field(..., description="Index of the image in the batch")
    blocks: List[ExtractedBlock] = Field(default_factory=list)
    success: bool = Field(True)
    error: Optional[str] = None


class DigitizeResponse(BaseModel):
    """Response from digitization."""

    id: str = Field(..., description="Note ID")
    title: str = Field(..., description="Note title")
    extracted_text: str = Field(..., description="Plain text extraction")
    latex_content: str = Field(..., description="LaTeX formatted content")
    blocks: List[ExtractedBlock] = Field(
        default_factory=list, description="Structured blocks"
    )
    success: bool = Field(True)
    error: Optional[str] = None
    image_count: int = Field(1, description="Number of images processed")
    merged: bool = Field(
        False, description="Whether content was merged from multiple images"
    )


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

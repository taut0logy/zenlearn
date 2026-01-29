"""
Content Tag Schemas - Pydantic models for structured content.

Defines the data structures for LLM-generated content that
will be parsed and rendered into PDF, PPTX, or Markdown.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from enum import Enum


class PageType(str, Enum):
    """Types of pages/slides."""
    TITLE = "title"
    CONTENT = "content"
    CODE = "code"
    SUMMARY = "summary"
    EXERCISE = "exercise"


class CalloutType(str, Enum):
    """Types of callout boxes."""
    INFO = "info"
    WARNING = "warning"
    TIP = "tip"
    EXAMPLE = "example"


class ImagePosition(str, Enum):
    """Image positioning options."""
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"


class DiagramType(str, Enum):
    """Mermaid diagram types."""
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS = "class"
    STATE = "state"
    ER = "er"
    GANTT = "gantt"
    PIE = "pie"


# ============================================
# Content Element Schemas
# ============================================

class HeadingSpec(BaseModel):
    """Heading element."""
    level: Literal[1, 2, 3] = 1
    text: str


class ImageSpec(BaseModel):
    """AI-generated image specification."""
    id: Optional[str] = None
    prompt: str = Field(..., description="Prompt for image generation")
    alt: str = Field(..., description="Alt text for accessibility")
    position: ImagePosition = ImagePosition.CENTER
    width: str = "80%"
    style: str = "educational, clean, minimalist"


class MermaidSpec(BaseModel):
    """Mermaid diagram specification."""
    id: Optional[str] = None
    diagram_type: DiagramType = DiagramType.FLOWCHART
    code: str
    caption: Optional[str] = None


class CodeBlockSpec(BaseModel):
    """Code block specification."""
    language: str = "python"
    code: str
    title: Optional[str] = None
    highlight_lines: Optional[List[int]] = None


class CalloutSpec(BaseModel):
    """Callout/alert box specification."""
    callout_type: CalloutType = CalloutType.INFO
    title: Optional[str] = None
    content: str


class ListItem(BaseModel):
    """List item with optional sub-items."""
    text: str
    sub_items: Optional[List[str]] = None


class ListSpec(BaseModel):
    """List specification."""
    list_type: Literal["bullet", "numbered"] = "bullet"
    items: List[ListItem]


class TableSpec(BaseModel):
    """Table specification."""
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None


class CitationSpec(BaseModel):
    """Citation/reference specification."""
    source: str
    page: Optional[str] = None
    section: Optional[str] = None


# ============================================
# Page/Slide Schema
# ============================================

class PageContent(BaseModel):
    """Content elements within a page."""
    headings: List[HeadingSpec] = []
    paragraphs: List[str] = []
    images: List[ImageSpec] = []
    diagrams: List[MermaidSpec] = []
    code_blocks: List[CodeBlockSpec] = []
    callouts: List[CalloutSpec] = []
    lists: List[ListSpec] = []
    tables: List[TableSpec] = []
    citations: List[CitationSpec] = []
    # Ordered sequence for rendering
    element_order: List[tuple] = []


class Page(BaseModel):
    """Single page or slide."""
    number: int
    page_type: PageType = PageType.CONTENT
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: PageContent = Field(default_factory=PageContent)
    speaker_notes: Optional[str] = None  # For PPTX


# ============================================
# Document Schema
# ============================================

class DocumentTheme(BaseModel):
    """Document visual theme."""
    primary_color: str = "#1a365d"
    secondary_color: str = "#2c5282"
    accent_color: str = "#3182ce"
    font_family: str = "Helvetica"
    style: str = "modern"  # Allow any style string from LLM



class DocumentSpec(BaseModel):
    """Complete document specification."""
    document_type: Literal["pdf", "pptx", "markdown"] = "markdown"
    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    course: Optional[str] = None
    date: Optional[str] = None
    pages: List[Page] = []
    theme: DocumentTheme = Field(default_factory=DocumentTheme)
    metadata: Dict[str, Any] = {}


# ============================================
# Lab/Code Generation Schemas
# ============================================

class TestCase(BaseModel):
    """Test case for code validation."""
    input: str
    expected_output: str
    description: Optional[str] = None
    is_hidden: bool = False


class CodeSpec(BaseModel):
    """Generated code specification."""
    language: str = "python"
    filename: str
    code: str
    description: str
    test_cases: List[TestCase] = []
    dependencies: List[str] = []


class LabSpec(BaseModel):
    """Lab exercise specification."""
    title: str
    description: str
    objectives: List[str] = []
    starter_code: Optional[CodeSpec] = None
    solution_code: Optional[CodeSpec] = None
    test_cases: List[TestCase] = []
    hints: List[str] = []
    difficulty: Literal["easy", "medium", "hard"] = "medium"


# ============================================
# Content Plan Schema
# ============================================

class VisualPlan(BaseModel):
    """Planned visual element."""
    visual_type: Literal["image", "diagram", "animation"] = "image"
    description: str
    position: Optional[str] = None


class SectionPlan(BaseModel):
    """Planned section structure."""
    title: str
    section_type: Literal["content", "code", "summary", "exercise"] = "content"
    key_points: List[str] = []
    visuals_needed: List[VisualPlan] = []
    code_examples: List[str] = []


class ContentPlan(BaseModel):
    """Complete content generation plan."""
    title: str
    output_type: Literal["pdf", "pptx", "markdown", "lab"] = "markdown"
    estimated_pages: int = 5
    sections: List[SectionPlan] = []
    visual_theme: DocumentTheme = Field(default_factory=DocumentTheme)
    target_audience: str = "University students"
    prerequisites: List[str] = []

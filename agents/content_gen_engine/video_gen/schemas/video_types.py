"""
Video Generation Schemas.

Data structures for the programmatic video generation pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Stages of the video generation pipeline."""
    SCRIPT_GENERATION = "script_generation"
    SCENE_PLANNING = "scene_planning"
    ASSET_GENERATION = "asset_generation"
    MANIM_GENERATION = "manim_generation"
    AUDIO_GENERATION = "audio_generation"
    VIDEO_COMPOSITION = "video_composition"
    COMPLETED = "completed"
    FAILED = "failed"


class SceneType(str, Enum):
    """Types of scenes in a video."""
    TITLE = "title"
    CONTENT = "content"
    CODE = "code"
    MANIM = "manim"
    DIAGRAM = "diagram"
    SUMMARY = "summary"


class VisualType(str, Enum):
    """Visual rendering type."""
    STATIC = "static"      # Static slide
    ANIMATED = "animated"  # Manim animation
    CODE_WALK = "code_walk"  # Code walkthrough with highlighting


# ============================================
# Script Schemas (Pydantic for LLM output)
# ============================================

class ScriptSegment(BaseModel):
    """A segment of narration with timing."""
    segment_id: str
    text: str
    duration_estimate: float = Field(description="Estimated duration in seconds")
    section: Literal["introduction", "main", "example", "code", "summary"] = "main"
    visual_suggestion: Optional[str] = None
    key_concepts: List[str] = []
    emphasis_words: List[str] = []
    pause_after: float = 0.5


class VideoScript(BaseModel):
    """Complete video script structure."""
    title: str
    hook: str = Field(description="Opening hook to grab attention")
    segments: List[ScriptSegment]
    total_duration_estimate: float
    key_takeaways: List[str] = []
    
    def get_full_text(self) -> str:
        """Get full narration text."""
        return " ".join(seg.text for seg in self.segments)


class SceneSpec(BaseModel):
    """Specification for a video scene."""
    scene_id: str
    segment_id: str  # Links to ScriptSegment
    scene_type: SceneType = SceneType.CONTENT
    title: Optional[str] = None
    content: Optional[str] = None
    visual_type: VisualType = VisualType.STATIC
    visual_description: Optional[str] = None
    
    # For code scenes
    code: Optional[str] = None
    code_language: str = "python"
    highlight_lines: List[int] = []
    
    # For Manim scenes
    manim_description: Optional[str] = None
    manim_code: Optional[str] = None
    
    duration: float = 5.0
    transition_in: str = "fade"
    transition_out: str = "fade"


class ScenePlan(BaseModel):
    """Complete scene plan for video."""
    scenes: List[SceneSpec]
    total_scenes: int = 0
    
    def model_post_init(self, __context):
        self.total_scenes = len(self.scenes)


# ============================================
# Code Walkthrough Schemas
# ============================================

class CodeAnnotation(BaseModel):
    """Annotation for a code section."""
    start_line: int
    end_line: int
    explanation: str
    highlight_type: Literal["focus", "add", "remove", "important"] = "focus"


class FunctionExplanation(BaseModel):
    """Explanation of a single function."""
    function_name: str
    signature: str
    purpose: str
    line_range: tuple = (0, 0)
    annotations: List[CodeAnnotation] = []
    narration: str = ""


class CodeWalkthrough(BaseModel):
    """Complete code walkthrough specification."""
    title: str
    full_code: str
    language: str = "python"
    overview: str = ""
    functions: List[FunctionExplanation] = []
    step_order: List[str] = []  # Order to explain functions


# ============================================
# Pipeline State (Dataclass for runtime)
# ============================================

@dataclass
class GeneratedAsset:
    """A generated asset (slide, animation, audio)."""
    asset_id: str
    asset_type: str  # "slide", "manim", "audio", "video"
    file_path: str
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineState:
    """Runtime state of the video generation pipeline."""
    job_id: str
    topic: str
    context: str = ""  # RAG context
    current_stage: PipelineStage = PipelineStage.SCRIPT_GENERATION
    
    # Generated content
    script: Optional[VideoScript] = None
    scene_plan: Optional[ScenePlan] = None
    
    # Generated assets
    slides: Dict[str, str] = field(default_factory=dict)  # scene_id -> path
    manim_videos: Dict[str, str] = field(default_factory=dict)
    audio_files: Dict[str, str] = field(default_factory=dict)  # segment_id -> path
    
    # Final outputs
    final_video_path: Optional[str] = None
    slides_output_dir: Optional[str] = None  # Deliverable: all slides
    
    # Tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    def set_stage(self, stage: PipelineStage):
        self.current_stage = stage


# ============================================
# Configuration
# ============================================

@dataclass
class VideoConfig:
    """Configuration for video generation."""
    resolution: tuple = (1920, 1080)
    fps: int = 30
    background_color: str = "#1a365d"
    text_color: str = "#ffffff"
    accent_color: str = "#3182ce"
    
    # TTS settings
    tts_voice: str = "en-US-AriaNeural"
    tts_rate: str = "+0%"
    
    # Manim settings
    manim_quality: str = "medium_quality"
    manim_max_retries: int = 3
    
    # Output settings
    output_format: str = "mp4"
    save_slides: bool = True  # Save slides as deliverables
    
    # Duration targets
    target_duration_minutes: float = 3.0


@dataclass
class ManimTemplate:
    """Pre-built Manim animation template."""
    name: str
    category: str  # "data_structure", "algorithm", "math"
    description: str
    code_template: str
    parameters: List[str]  # Required template parameters

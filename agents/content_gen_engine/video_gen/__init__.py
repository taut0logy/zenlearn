"""
Video Generation Engine.

Programmatic educational video generation with Manim, TTS, and FFmpeg.
"""

from content_gen_engine.video_gen.pipeline import (
    VideoPipeline,
    get_video_pipeline,
)
from content_gen_engine.video_gen.schemas import (
    VideoScript,
    ScriptSegment,
    SceneSpec,
    ScenePlan,
    SceneType,
    VisualType,
    PipelineState,
    PipelineStage,
    VideoConfig,
    CodeWalkthrough,
)
from content_gen_engine.video_gen.agents import (
    ScriptWriterAgent,
    ScenePlannerAgent,
    get_script_writer,
    get_scene_planner,
)
from content_gen_engine.video_gen.generators import (
    SlideRenderer,
    ManimGenerator,
    TTSEngine,
    get_slide_renderer,
    get_manim_generator,
    get_tts_engine,
)
from content_gen_engine.video_gen.composers import (
    VideoComposer,
    get_video_composer,
)

__all__ = [
    # Pipeline
    "VideoPipeline",
    "get_video_pipeline",
    
    # Schemas
    "VideoScript",
    "ScriptSegment",
    "SceneSpec",
    "ScenePlan",
    "SceneType",
    "VisualType",
    "PipelineState",
    "PipelineStage",
    "VideoConfig",
    "CodeWalkthrough",
    
    # Agents
    "ScriptWriterAgent",
    "ScenePlannerAgent",
    "get_script_writer",
    "get_scene_planner",
    
    # Generators
    "SlideRenderer",
    "ManimGenerator",
    "TTSEngine",
    "get_slide_renderer",
    "get_manim_generator",
    "get_tts_engine",
    
    # Composers
    "VideoComposer",
    "get_video_composer",
]

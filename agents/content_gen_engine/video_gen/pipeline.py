"""
Video Generation Pipeline.

Main orchestrator for programmatic video generation.
"""

import os
import uuid
import shutil
from typing import Optional
from pathlib import Path
from datetime import datetime

from content_gen_engine.video_gen.schemas.video_types import (
    VideoScript, ScenePlan, PipelineState, PipelineStage, VideoConfig
)
from content_gen_engine.video_gen.agents.script_writer import get_script_writer
from content_gen_engine.video_gen.agents.scene_planner import get_scene_planner
from content_gen_engine.video_gen.generators.slide_renderer import get_slide_renderer
from content_gen_engine.video_gen.generators.manim_generator import get_manim_generator
from content_gen_engine.video_gen.generators.tts_engine import get_tts_engine
from content_gen_engine.video_gen.composers.video_composer import get_video_composer
from utils.logger import logger


class VideoPipeline:
    """
    Main video generation pipeline.
    
    Orchestrates:
    1. Script generation (topic → narration)
    2. Scene planning (script → visual specs)
    3. Asset generation (slides + Manim)
    4. Audio generation (TTS)
    5. Video composition (final assembly)
    
    Features:
    - RAG context integration
    - Manim with syntax-fix loop
    - Slide deliverables saved
    - Graceful fallbacks
    """
    
    def __init__(
        self,
        output_dir: str = "./output",
        config: Optional[VideoConfig] = None
    ):
        self.output_dir = Path(output_dir)
        self.config = config or VideoConfig()
        
        # Initialize components
        self.script_writer = get_script_writer(self.config)
        self.scene_planner = get_scene_planner(self.config)
        self.slide_renderer = None  # Lazy init
        self.manim_generator = None
        self.tts_engine = None
        self.video_composer = None
    
    async def generate(
        self,
        topic: str,
        context: str = "",
        duration_minutes: float = None,
        code: Optional[str] = None
    ) -> PipelineState:
        """
        Generate educational video.
        
        Args:
            topic: Topic to explain
            context: RAG context from course materials
            duration_minutes: Target duration
            code: Optional code for code walkthrough
            
        Returns:
            PipelineState with results
        """
        job_id = str(uuid.uuid4())[:8]
        job_dir = self.output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        state = PipelineState(
            job_id=job_id,
            topic=topic,
            context=context
        )
        
        logger.info(f"Starting video generation: {job_id} | Topic: {topic}")
        
        duration = (duration_minutes or self.config.target_duration_minutes) * 60
        
        try:
            # Stage 1: Script Generation
            state.set_stage(PipelineStage.SCRIPT_GENERATION)
            logger.info(f"[{job_id}] Stage 1: Generating script...")
            
            if code:
                state.script = await self.script_writer.generate_code_script(
                    code=code,
                    topic=topic,
                    duration_seconds=duration
                )
            else:
                state.script = await self.script_writer.generate(
                    topic=topic,
                    context=context,
                    duration_seconds=duration
                )
            
            logger.info(f"[{job_id}] Script: {state.script.title} ({len(state.script.segments)} segments)")
            
            # Stage 2: Scene Planning
            state.set_stage(PipelineStage.SCENE_PLANNING)
            logger.info(f"[{job_id}] Stage 2: Planning scenes...")
            
            if code:
                state.scene_plan = await self.scene_planner.plan_code_walkthrough(
                    code=code,
                    script=state.script
                )
            else:
                state.scene_plan = await self.scene_planner.plan(state.script)
            
            logger.info(f"[{job_id}] Planned {state.scene_plan.total_scenes} scenes")
            
            # Stage 3: Asset Generation
            state.set_stage(PipelineStage.ASSET_GENERATION)
            logger.info(f"[{job_id}] Stage 3: Generating assets...")
            
            # Initialize generators with job-specific paths
            slides_dir = job_dir / "slides"
            slides_dir.mkdir(exist_ok=True)
            self.slide_renderer = get_slide_renderer(str(slides_dir), self.config)
            
            manim_dir = job_dir / "manim"
            manim_dir.mkdir(exist_ok=True)
            self.manim_generator = get_manim_generator(str(manim_dir), self.config)
            
            # Generate slides
            state.slides = await self.slide_renderer.render_all(state.scene_plan.scenes)
            logger.info(f"[{job_id}] Rendered {len(state.slides)} slides")
            
            # Save slides as deliverable
            if self.config.save_slides:
                state.slides_output_dir = str(slides_dir)
            
            # Stage 4: Manim Generation (with fix loop)
            state.set_stage(PipelineStage.MANIM_GENERATION)
            logger.info(f"[{job_id}] Stage 4: Generating Manim animations...")
            
            manim_scenes = [s for s in state.scene_plan.scenes if s.visual_type.value == "animated"]
            if manim_scenes:
                state.manim_videos = await self.manim_generator.render_all(manim_scenes)
                logger.info(f"[{job_id}] Generated {len(state.manim_videos)} Manim animations")
                
                # If Manim failed, these scenes already have fallback slides
            
            # Stage 5: Audio Generation
            state.set_stage(PipelineStage.AUDIO_GENERATION)
            logger.info(f"[{job_id}] Stage 5: Generating audio...")
            
            audio_dir = job_dir / "audio"
            audio_dir.mkdir(exist_ok=True)
            self.tts_engine = get_tts_engine(str(audio_dir))
            
            state.audio_files = await self.tts_engine.synthesize_script(state.script)
            logger.info(f"[{job_id}] Generated {len(state.audio_files)} audio segments")
            
            # Stage 6: Video Composition
            state.set_stage(PipelineStage.VIDEO_COMPOSITION)
            logger.info(f"[{job_id}] Stage 6: Composing video...")
            
            video_dir = job_dir / "video"
            video_dir.mkdir(exist_ok=True)
            self.video_composer = get_video_composer(str(video_dir))
            
            output_name = self._sanitize_filename(state.script.title)
            state.final_video_path = await self.video_composer.compose(
                slides=state.slides,
                audio_files=state.audio_files,
                scene_plan=state.scene_plan,
                manim_videos=state.manim_videos,
                output_name=output_name
            )
            
            # Complete
            state.set_stage(PipelineStage.COMPLETED)
            state.completed_at = datetime.now()
            
            logger.info(f"[{job_id}] ✓ Video generation complete: {state.final_video_path}")
            logger.info(f"[{job_id}] ✓ Slides saved to: {state.slides_output_dir}")
            
            return state
            
        except Exception as e:
            state.set_stage(PipelineStage.FAILED)
            state.add_error(str(e))
            logger.error(f"[{job_id}] Pipeline failed: {e}")
            raise
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for filename."""
        return "".join(c if c.isalnum() or c in '-_ ' else '' for c in name)[:50].strip().replace(' ', '_')


def get_video_pipeline(
    output_dir: str = "./output",
    config: Optional[VideoConfig] = None
) -> VideoPipeline:
    """Factory for video pipeline."""
    return VideoPipeline(output_dir, config)

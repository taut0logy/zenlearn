"""
Video Composer.

FFmpeg-based video assembly combining slides, animations, and audio.
"""

import subprocess
import os
import shutil
from typing import Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass

from content_gen_engine.video_gen.schemas.video_types import (
    ScenePlan, VideoConfig, PipelineState
)
from utils.logger import logger


@dataclass  
class CompositionConfig:
    """Video composition settings."""
    fps: int = 30
    codec: str = "libx264"
    audio_codec: str = "aac"
    preset: str = "medium"
    crf: int = 23  # Quality (lower = better)
    
    transition_duration: float = 0.5
    fade_duration: float = 0.3


class VideoComposer:
    """
    Composes final video from slides, animations, and audio.
    
    Uses FFmpeg for:
    - Image sequence to video
    - Audio sync
    - Scene concatenation
    - Transitions
    """
    
    def __init__(
        self,
        output_dir: str = "./output/video",
        config: Optional[CompositionConfig] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or CompositionConfig()
        
        # Check FFmpeg
        self._ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("FFmpeg available")
                return True
            return False
        except:
            logger.warning("FFmpeg not found")
            return False
    
    async def compose(
        self,
        slides: Dict[str, str],
        audio_files: Dict[str, str],
        scene_plan: ScenePlan,
        manim_videos: Optional[Dict[str, str]] = None,
        output_name: str = "output"
    ) -> Optional[str]:
        """
        Compose final video.
        
        Args:
            slides: scene_id -> slide image path
            audio_files: segment_id -> audio path
            scene_plan: Scene specifications
            manim_videos: scene_id -> manim video path
            output_name: Output filename
            
        Returns:
            Path to final video
        """
        if not self._ffmpeg_available:
            logger.error("FFmpeg not available")
            return None
        
        manim_videos = manim_videos or {}
        temp_videos = []
        
        try:
            # Create video for each scene
            for scene in scene_plan.scenes:
                scene_video = await self._create_scene_video(
                    scene_id=scene.scene_id,
                    segment_id=scene.segment_id,
                    slides=slides,
                    audio_files=audio_files,
                    manim_videos=manim_videos,
                    duration=scene.duration
                )
                
                if scene_video:
                    temp_videos.append(scene_video)
            
            if not temp_videos:
                logger.error("No scene videos created")
                return None
            
            # Concatenate all scenes
            final_path = self.output_dir / f"{output_name}.mp4"
            await self._concatenate_videos(temp_videos, str(final_path))
            
            logger.info(f"Video composed: {final_path}")
            return str(final_path)
            
        finally:
            # Cleanup temp videos
            for temp in temp_videos:
                try:
                    os.unlink(temp)
                except:
                    pass
    
    async def _create_scene_video(
        self,
        scene_id: str,
        segment_id: str,
        slides: Dict[str, str],
        audio_files: Dict[str, str],
        manim_videos: Dict[str, str],
        duration: float
    ) -> Optional[str]:
        """Create video for a single scene."""
        output_path = self.output_dir / f"temp_{scene_id}.mp4"
        
        # Use Manim video if available
        if scene_id in manim_videos:
            video_input = manim_videos[scene_id]
            
            # Add audio if available
            if segment_id in audio_files:
                await self._add_audio_to_video(
                    video_input,
                    audio_files[segment_id],
                    str(output_path)
                )
            else:
                # Copy video as-is (use shutil for Windows compatibility)
                shutil.copy(video_input, str(output_path))
            
            return str(output_path)
        
        # Use slide image
        if scene_id in slides:
            slide_path = slides[scene_id]
            audio_path = audio_files.get(segment_id)
            
            await self._image_to_video(
                image_path=slide_path,
                audio_path=audio_path,
                output_path=str(output_path),
                duration=duration
            )
            
            return str(output_path)
        
        return None
    
    async def _image_to_video(
        self,
        image_path: str,
        audio_path: Optional[str],
        output_path: str,
        duration: float
    ):
        """Convert image to video with audio."""
        if audio_path and os.path.exists(audio_path):
            # Use audio duration
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', image_path,
                '-i', audio_path,
                '-c:v', self.config.codec,
                '-c:a', self.config.audio_codec,
                '-preset', self.config.preset,
                '-crf', str(self.config.crf),
                '-pix_fmt', 'yuv420p',
                '-shortest',
                output_path
            ]
        else:
            # Use fixed duration
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', image_path,
                '-t', str(duration),
                '-c:v', self.config.codec,
                '-preset', self.config.preset,
                '-crf', str(self.config.crf),
                '-pix_fmt', 'yuv420p',
                output_path
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Image to video failed: {result.stderr}")
    
    async def _add_audio_to_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ):
        """Add audio track to video."""
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', self.config.audio_codec,
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
    
    async def _concatenate_videos(
        self,
        video_paths: List[str],
        output_path: str
    ):
        """Concatenate multiple videos."""
        # Create concat file with absolute paths
        concat_file = self.output_dir / "concat.txt"
        
        with open(concat_file, 'w') as f:
            for path in video_paths:
                # Use absolute paths to avoid cwd issues
                abs_path = Path(path).resolve()
                # Escape backslashes for FFmpeg on Windows
                escaped_path = str(abs_path).replace('\\', '/')
                f.write(f"file '{escaped_path}'\n")
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c:v', self.config.codec,
            '-c:a', self.config.audio_codec,
            '-preset', self.config.preset,
            '-crf', str(self.config.crf),
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Cleanup
        concat_file.unlink()
        
        if result.returncode != 0:
            logger.error(f"Concatenation failed: {result.stderr}")
    
    async def add_subtitles(
        self,
        video_path: str,
        subtitles_path: str,
        output_path: str
    ):
        """Add subtitles to video."""
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', f"subtitles={subtitles_path}",
            '-c:a', 'copy',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)


def get_video_composer(
    output_dir: str = "./output/video",
    config: Optional[CompositionConfig] = None
) -> VideoComposer:
    """Factory for video composer."""
    return VideoComposer(output_dir, config)

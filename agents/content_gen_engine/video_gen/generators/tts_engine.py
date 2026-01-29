"""
TTS Engine.

Text-to-Speech using Edge TTS for educational video narration.
"""

import asyncio
import os
import re
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from content_gen_engine.video_gen.schemas.video_types import (
    ScriptSegment, VideoScript, VideoConfig
)
from utils.logger import logger


@dataclass
class TTSConfig:
    """TTS configuration."""
    voice: str = "en-US-AriaNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    output_format: str = "mp3"


# Available Edge TTS voices
VOICES = {
    "aria": "en-US-AriaNeural",       # Female, warm
    "guy": "en-US-GuyNeural",         # Male, professional  
    "jenny": "en-US-JennyNeural",     # Female, friendly
    "davis": "en-US-DavisNeural",     # Male, casual
    "andrew": "en-US-AndrewNeural",   # Male, engaging
    "emma": "en-US-EmmaNeural",       # Female, clear
}


class TTSEngine:
    """
    Text-to-Speech engine using Edge TTS.
    
    Features:
    - High-quality neural voices (free)
    - SSML support for pauses and emphasis
    - Word-level timing for sync
    - Batch synthesis
    """
    
    def __init__(
        self,
        output_dir: str = "./output/audio",
        config: Optional[TTSConfig] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or TTSConfig()
    
    async def synthesize(
        self,
        text: str,
        output_id: str,
        voice: Optional[str] = None
    ) -> str:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to speak
            output_id: Output file identifier
            voice: Optional voice override
            
        Returns:
            Path to audio file
        """
        try:
            import edge_tts
        except ImportError:
            logger.error("edge-tts not installed. Run: pip install edge-tts")
            raise
        
        # Process text
        processed = self._preprocess_text(text)
        
        # Resolve voice
        voice_name = voice or self.config.voice
        if voice_name in VOICES:
            voice_name = VOICES[voice_name]
        
        output_path = self.output_dir / f"{output_id}.{self.config.output_format}"
        
        # Generate
        communicate = edge_tts.Communicate(
            text=processed,
            voice=voice_name,
            rate=self.config.rate,
            pitch=self.config.pitch
        )
        
        await communicate.save(str(output_path))
        
        logger.info(f"TTS generated: {output_path}")
        return str(output_path)
    
    async def synthesize_with_timing(
        self,
        text: str,
        output_id: str,
        voice: Optional[str] = None
    ) -> Tuple[str, List[dict]]:
        """
        Synthesize and get word timings for sync.
        
        Returns:
            (audio_path, word_timings)
        """
        try:
            import edge_tts
        except ImportError:
            raise ImportError("edge-tts not installed")
        
        processed = self._preprocess_text(text)
        voice_name = voice or self.config.voice
        if voice_name in VOICES:
            voice_name = VOICES[voice_name]
        
        output_path = self.output_dir / f"{output_id}.{self.config.output_format}"
        
        communicate = edge_tts.Communicate(
            text=processed,
            voice=voice_name,
            rate=self.config.rate
        )
        
        # Collect word boundaries
        word_timings = []
        audio_chunks = []
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_timings.append({
                    'word': chunk.get('text', ''),
                    'offset': chunk.get('offset', 0) / 10000000,  # To seconds
                    'duration': chunk.get('duration', 0) / 10000000
                })
        
        # Write audio
        with open(output_path, 'wb') as f:
            for chunk in audio_chunks:
                f.write(chunk)
        
        return str(output_path), word_timings
    
    async def synthesize_script(
        self,
        script: VideoScript,
        max_concurrent: int = 3
    ) -> Dict[str, str]:
        """
        Synthesize all script segments.
        
        Returns:
            Dict mapping segment_id to audio path
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def synth_segment(segment: ScriptSegment):
            async with semaphore:
                path = await self.synthesize(
                    segment.text,
                    segment.segment_id
                )
                return segment.segment_id, path
        
        tasks = [synth_segment(seg) for seg in script.segments]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        audio_files = {}
        for result in results:
            if isinstance(result, tuple):
                seg_id, path = result
                audio_files[seg_id] = path
            else:
                logger.error(f"TTS failed: {result}")
        
        logger.info(f"Synthesized {len(audio_files)} audio segments")
        return audio_files
    
    def _preprocess_text(self, text: str) -> str:
        """Clean text for TTS - remove markdown and special tags."""
        # Remove [PAUSE] markers - replace with comma for natural pause
        text = re.sub(r'\[PAUSE\]', ', ', text)
        text = re.sub(r'\[LONG_PAUSE\]', '. ', text)
        
        # Remove markdown emphasis markers but keep the text
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold** -> bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # *italic* -> italic
        text = re.sub(r'__(.+?)__', r'\1', text)      # __bold__ -> bold
        text = re.sub(r'_(.+?)_', r'\1', text)        # _italic_ -> italic
        
        # Remove code backticks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Code blocks
        text = re.sub(r'`(.+?)`', r'\1', text)        # Inline code -> just text
        
        # Remove XML/HTML-like tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove markdown headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # Remove markdown links [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove markdown images ![alt](url)
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
        
        # Clean multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Handle abbreviations for natural speech
        replacements = {
            'e.g.': 'for example',
            'i.e.': 'that is',
            'etc.': 'et cetera',
            'vs.': 'versus',
            'w/': 'with',
            'w/o': 'without',
            'O(n)': 'O of n',
            'O(1)': 'O of 1',
            'O(log n)': 'O of log n',
            'O(n^2)': 'O of n squared',
            '->': 'to',
            '=>': 'implies',
        }
        for abbr, full in replacements.items():
            text = text.replace(abbr, full)
        
        return text.strip()
    
    async def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds."""
        try:
            import subprocess
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    audio_path
                ],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except:
            # Fallback estimate
            return 0.0


def get_tts_engine(
    output_dir: str = "./output/audio",
    config: Optional[TTSConfig] = None
) -> TTSEngine:
    """Factory for TTS engine."""
    return TTSEngine(output_dir, config)

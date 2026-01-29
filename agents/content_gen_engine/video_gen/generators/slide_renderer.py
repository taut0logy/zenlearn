"""
Slide Renderer.

Generates static slide images using PIL.
No LaTeX dependency - pure Python rendering.
"""

import os
from typing import Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

from content_gen_engine.video_gen.schemas.video_types import (
    SceneSpec, SceneType, VideoConfig
)
from utils.logger import logger


@dataclass
class SlideStyle:
    """Slide styling configuration."""
    background: str = "#1a365d"
    title_color: str = "#ffffff"
    text_color: str = "#e2e8f0"
    accent_color: str = "#3182ce"
    code_bg: str = "#0d1117"
    code_color: str = "#c9d1d9"
    
    # Font sizes (increased for 1080p readability)
    title_size: int = 120
    subtitle_size: int = 80
    body_size: int = 56
    code_size: int = 40
    
    padding: int = 100
    line_spacing: float = 1.6


class SlideRenderer:
    """
    Renders static slides as PNG images.
    
    Supports:
    - Title slides
    - Content slides with text
    - Code slides with syntax highlighting
    - Summary slides
    """
    
    def __init__(
        self,
        output_dir: str = "./output/slides",
        config: Optional[VideoConfig] = None,
        style: Optional[SlideStyle] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or VideoConfig()
        self.style = style or SlideStyle()
        
        # Try to load nice fonts
        self._title_font = self._load_font(self.style.title_size)
        self._subtitle_font = self._load_font(self.style.subtitle_size)
        self._body_font = self._load_font(self.style.body_size)
        self._code_font = self._load_font(self.style.code_size, monospace=True)
    
    def _load_font(self, size: int, monospace: bool = False) -> ImageFont.FreeTypeFont:
        """Load font with fallback using full paths for Windows."""
        import platform
        
        # Windows font paths
        if platform.system() == "Windows":
            font_dir = "C:/Windows/Fonts/"
            font_files = (
                ["consola.ttf", "cour.ttf", "lucon.ttf"]
                if monospace else
                ["arial.ttf", "calibri.ttf", "segoeui.ttf", "verdana.ttf"]
            )
            for font_file in font_files:
                try:
                    return ImageFont.truetype(font_dir + font_file, size)
                except:
                    continue
        
        # Try system font names (Linux/Mac)
        font_names = (
            ["DejaVuSansMono", "Consolas", "Monaco", "Courier"]
            if monospace else
            ["DejaVuSans", "Arial", "Helvetica", "FreeSans"]
        )
        
        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except:
                continue
        
        # Final fallback with size (PIL >= 10.0)
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            # Older PIL - default is tiny but better than nothing
            return ImageFont.load_default()
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def render(self, scene: SceneSpec) -> str:
        """
        Render a scene to slide image.
        
        Returns:
            Path to rendered PNG
        """
        width, height = self.config.resolution
        
        # Create canvas
        bg_color = self._hex_to_rgb(self.style.background)
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # Render based on scene type
        if scene.scene_type == SceneType.TITLE:
            self._render_title_slide(draw, scene, width, height)
        elif scene.scene_type == SceneType.CODE:
            self._render_code_slide(draw, scene, width, height)
        elif scene.scene_type == SceneType.SUMMARY:
            self._render_summary_slide(draw, scene, width, height)
        else:
            self._render_content_slide(draw, scene, width, height)
        
        # Save
        output_path = self.output_dir / f"{scene.scene_id}.png"
        image.save(output_path, "PNG")
        
        logger.info(f"Rendered slide: {output_path}")
        return str(output_path)
    
    def _render_title_slide(
        self,
        draw: ImageDraw.Draw,
        scene: SceneSpec,
        width: int,
        height: int
    ):
        """Render title slide with centered text."""
        title = scene.title or "Untitled"
        subtitle = scene.content or ""
        
        # Center title
        title_color = self._hex_to_rgb(self.style.title_color)
        
        # Get text size
        bbox = draw.textbbox((0, 0), title, font=self._title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2 - 50
        
        draw.text((x, y), title, fill=title_color, font=self._title_font)
        
        # Subtitle
        if subtitle:
            bbox = draw.textbbox((0, 0), subtitle, font=self._subtitle_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y += text_height + 40
            
            sub_color = self._hex_to_rgb(self.style.text_color)
            draw.text((x, y), subtitle, fill=sub_color, font=self._subtitle_font)
    
    def _render_content_slide(
        self,
        draw: ImageDraw.Draw,
        scene: SceneSpec,
        width: int,
        height: int
    ):
        """Render content slide with title and body."""
        padding = self.style.padding
        
        # Title
        if scene.title:
            title_color = self._hex_to_rgb(self.style.title_color)
            draw.text(
                (padding, padding),
                scene.title,
                fill=title_color,
                font=self._subtitle_font
            )
            y_offset = padding + self.style.subtitle_size + 40
        else:
            y_offset = padding
        
        # Content
        if scene.content:
            text_color = self._hex_to_rgb(self.style.text_color)
            
            # Word wrap
            wrapped = self._wrap_text(
                scene.content,
                self._body_font,
                width - 2 * padding
            )
            
            for line in wrapped:
                draw.text(
                    (padding, y_offset),
                    line,
                    fill=text_color,
                    font=self._body_font
                )
                y_offset += int(self.style.body_size * self.style.line_spacing)
    
    def _render_code_slide(
        self,
        draw: ImageDraw.Draw,
        scene: SceneSpec,
        width: int,
        height: int
    ):
        """Render code slide with syntax highlighting."""
        padding = self.style.padding
        code_padding = 30
        
        # Title
        y_offset = padding
        if scene.title:
            title_color = self._hex_to_rgb(self.style.title_color)
            draw.text(
                (padding, y_offset),
                scene.title,
                fill=title_color,
                font=self._subtitle_font
            )
            y_offset += self.style.subtitle_size + 30
        
        # Code box
        if scene.code:
            code_bg = self._hex_to_rgb(self.style.code_bg)
            code_color = self._hex_to_rgb(self.style.code_color)
            
            # Draw code background
            code_box = (
                padding,
                y_offset,
                width - padding,
                height - padding
            )
            draw.rectangle(code_box, fill=code_bg)
            
            # Draw code lines
            lines = scene.code.split('\n')
            line_height = int(self.style.code_size * 1.4)
            
            for i, line in enumerate(lines):
                line_y = y_offset + code_padding + i * line_height
                
                if line_y > height - padding - line_height:
                    break
                
                # Highlight lines if specified
                if scene.highlight_lines and (i + 1) in scene.highlight_lines:
                    highlight_color = (50, 100, 150)
                    draw.rectangle(
                        (padding, line_y - 5, width - padding, line_y + line_height - 5),
                        fill=highlight_color
                    )
                
                draw.text(
                    (padding + code_padding, line_y),
                    line,
                    fill=code_color,
                    font=self._code_font
                )
    
    def _render_summary_slide(
        self,
        draw: ImageDraw.Draw,
        scene: SceneSpec,
        width: int,
        height: int
    ):
        """Render summary slide with key takeaways."""
        padding = self.style.padding
        
        # Title
        title = scene.title or "Key Takeaways"
        title_color = self._hex_to_rgb(self.style.title_color)
        draw.text(
            (padding, padding),
            title,
            fill=title_color,
            font=self._subtitle_font
        )
        
        y_offset = padding + self.style.subtitle_size + 50
        
        # Bullet points
        if scene.content:
            text_color = self._hex_to_rgb(self.style.text_color)
            accent = self._hex_to_rgb(self.style.accent_color)
            
            points = scene.content.split('\n')
            for point in points:
                if not point.strip():
                    continue
                
                # Bullet
                draw.ellipse(
                    (padding, y_offset + 10, padding + 15, y_offset + 25),
                    fill=accent
                )
                
                # Text
                draw.text(
                    (padding + 35, y_offset),
                    point.strip(),
                    fill=text_color,
                    font=self._body_font
                )
                
                y_offset += int(self.style.body_size * 2)
    
    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int
    ) -> List[str]:
        """Word wrap text to fit width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            
            if bbox[2] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    async def render_all(self, scenes: List[SceneSpec]) -> dict:
        """
        Render all static scenes.
        
        Returns:
            Dict mapping scene_id to file path
        """
        results = {}
        
        for scene in scenes:
            # Only render static slides, not manim scenes
            if scene.visual_type.value != "animated":
                path = self.render(scene)
                results[scene.scene_id] = path
        
        logger.info(f"Rendered {len(results)} slides")
        return results


def get_slide_renderer(
    output_dir: str = "./output/slides",
    config: Optional[VideoConfig] = None
) -> SlideRenderer:
    """Factory for slide renderer."""
    return SlideRenderer(output_dir, config)

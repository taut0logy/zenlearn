"""
Manim Animation Generator.

Generates and renders Manim animations with syntax-fix loop.
Falls back to static diagram on failure.
"""

import subprocess
import os
import re
import sys
import tempfile
import shutil
from typing import Optional, Dict
from pathlib import Path

from content_gen_engine.video_gen.schemas.video_types import (
    SceneSpec, VideoConfig, ManimTemplate
)
from services.gemini_service import get_gemini_service
from utils.logger import logger


# Pre-built Manim templates
MANIM_TEMPLATES: Dict[str, ManimTemplate] = {
    "array_visualization": ManimTemplate(
        name="Array Visualization",
        category="data_structure",
        description="Visualize array with highlighting",
        code_template='''from manim import *

class GeneratedScene(Scene):
    def construct(self):
        title = Text("{title}", font_size=42)
        self.play(Write(title))
        self.play(title.animate.to_edge(UP))
        
        values = {values}
        squares = VGroup(*[
            VGroup(
                Square(side_length=0.8, color=BLUE),
                Text(str(v), font_size=24)
            ).arrange(ORIGIN)
            for v in values
        ]).arrange(RIGHT, buff=0.1)
        
        self.play(Create(squares), run_time=1.5)
        self.wait(0.5)
        
        # Highlight elements
        for i in {highlight_indices}:
            self.play(squares[i][0].animate.set_color(YELLOW))
            self.wait(0.3)
        
        self.wait(1)
''',
        parameters=["title", "values", "highlight_indices"]
    ),
    
    "binary_search": ManimTemplate(
        name="Binary Search Animation",
        category="algorithm",
        description="Step-by-step binary search visualization",
        code_template='''from manim import *

class GeneratedScene(Scene):
    def construct(self):
        title = Text("Binary Search", font_size=48)
        self.play(Write(title))
        self.play(title.animate.to_edge(UP))
        
        # Create sorted array
        values = {values}
        target = {target}
        
        squares = VGroup(*[
            VGroup(
                Square(side_length=0.8, color=BLUE),
                Text(str(v), font_size=20)
            ).arrange(ORIGIN)
            for v in values
        ]).arrange(RIGHT, buff=0.05).move_to(ORIGIN)
        
        self.play(Create(squares))
        
        # Binary search visualization
        left, right = 0, len(values) - 1
        while left <= right:
            mid = (left + right) // 2
            
            # Highlight search range
            for i in range(len(values)):
                if left <= i <= right:
                    squares[i][0].set_color(BLUE)
                else:
                    squares[i][0].set_color(GRAY)
            
            # Highlight mid
            self.play(squares[mid][0].animate.set_color(YELLOW))
            self.wait(0.5)
            
            if values[mid] == target:
                self.play(squares[mid][0].animate.set_color(GREEN))
                break
            elif values[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        self.wait(1)
''',
        parameters=["values", "target"]
    )
}


class ManimGenerator:
    """
    Generates and renders Manim animations.
    
    Features:
    - LLM-generated Manim code from description
    - Syntax validation with compile-fix loop
    - Pre-built templates for common animations
    - Fallback to static diagram on failure
    """
    
    GENERATION_PROMPT = '''Generate Manim Community Edition code for this animation.

<description>
{description}
</description>

<duration>
Target duration: {duration} seconds
</duration>

<strict_rules>
1. Output ONLY Python code - no markdown, no explanations, no backticks
2. Scene class MUST be named exactly: GeneratedScene
3. Start with: from manim import *
4. Keep animations SIMPLE - avoid complex 3D or advanced features
5. Use only these safe mobjects: Text, MathTex, Square, Circle, Line, Arrow, VGroup, Rectangle
6. Use only these safe animations: Write, Create, FadeIn, FadeOut, Transform, ReplacementTransform
7. Always end with self.wait(1)
</strict_rules>

<complete_working_example>
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Title
        title = Text("Array Visualization", font_size=48)
        self.play(Write(title), run_time=1)
        self.play(title.animate.to_edge(UP))
        
        # Create array elements
        squares = VGroup()
        for i, val in enumerate([1, 3, 5, 7, 9]):
            sq = Square(side_length=0.8, color=BLUE)
            txt = Text(str(val), font_size=24)
            group = VGroup(sq, txt)
            squares.add(group)
        squares.arrange(RIGHT, buff=0.2)
        
        self.play(Create(squares), run_time=1.5)
        self.wait(0.5)
        
        # Highlight middle element
        self.play(squares[2][0].animate.set_color(YELLOW), run_time=0.5)
        
        self.wait(1)
</complete_working_example>

Generate code for the description above. Output ONLY the Python code:'''

    FIX_PROMPT = '''The following Manim code has an error. Fix it.

<broken_code>
{code}
</broken_code>

<error_message>
{error}
</error_message>

<fix_rules>
1. Output ONLY fixed Python code - no markdown, no backticks, no explanations
2. Keep class name as GeneratedScene
3. Start with: from manim import *
4. If error is about missing imports, add them
5. If error is about syntax, fix the syntax
6. If error is about undefined variables, define them
7. Simplify complex animations that might fail
</fix_rules>

Output ONLY the corrected Python code:'''

    def __init__(
        self,
        output_dir: str = "./output/manim",
        config: Optional[VideoConfig] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or VideoConfig()
        self.llm = get_gemini_service("pro")
        
        # Check if manim is available
        self._manim_available = self._check_manim()
    
    def _check_manim(self) -> bool:
        """Check if manim CLI is available."""
        try:
            # Use python -m manim for Windows venv compatibility
            result = subprocess.run(
                [sys.executable, '-m', 'manim', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Manim available: {result.stdout.strip()}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Manim not found: {e}. Install with: pip install manim")
            return False
    
    async def generate(
        self,
        scene: SceneSpec,
        use_template: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate and render Manim animation.
        
        Args:
            scene: Scene specification with manim_description
            use_template: Optional template name
            
        Returns:
            Path to rendered video or None on failure
        """
        if not self._manim_available:
            logger.warning("Manim unavailable, skipping animation")
            return None
        
        # Try template first if specified
        if use_template and use_template in MANIM_TEMPLATES:
            code = self._apply_template(use_template, scene)
        else:
            # Generate code with LLM
            code = await self._generate_code(scene)
        
        if not code:
            return None
        
        # Render with retry loop
        for attempt in range(self.config.manim_max_retries):
            success, result = await self._try_render(scene.scene_id, code)
            
            if success:
                return result
            
            # Fix code with LLM
            if attempt < self.config.manim_max_retries - 1:
                logger.info(f"Manim attempt {attempt + 1} failed, fixing...")
                code = await self._fix_code(code, result)
                
                if not code:
                    break
        
        logger.error(f"Manim generation failed after {self.config.manim_max_retries} attempts")
        return None
    
    async def _generate_code(self, scene: SceneSpec) -> Optional[str]:
        """Generate Manim code from description."""
        description = scene.manim_description or scene.visual_description or scene.content
        
        if not description:
            logger.warning("No description for Manim generation")
            return None
        
        prompt = self.GENERATION_PROMPT.format(
            description=description,
            duration=scene.duration
        )
        
        try:
            response = await self.llm.generate(prompt)
            code = self._extract_code(response)
            return code
        except Exception as e:
            logger.error(f"Manim code generation failed: {e}")
            return None
    
    async def _fix_code(self, code: str, error: str) -> Optional[str]:
        """Fix Manim code using LLM."""
        prompt = self.FIX_PROMPT.format(code=code, error=error)
        
        try:
            response = await self.llm.generate(prompt)
            fixed = self._extract_code(response)
            logger.info("Manim code fixed by LLM")
            return fixed
        except Exception as e:
            logger.error(f"Manim fix failed: {e}")
            return None
    
    async def _try_render(
        self,
        scene_id: str,
        code: str
    ) -> tuple:
        """
        Try to render Manim code.
        
        Returns:
            (success, video_path or error_message)
        """
        # Validate syntax first
        try:
            compile(code, '<manim>', 'exec')
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        
        # Write to temp file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir=str(self.output_dir)
        )
        temp_file.write(code)
        temp_file.close()
        
        try:
            # Render
            quality_flag = f"-q{self.config.manim_quality[0]}"
            output_path = self.output_dir / f"{scene_id}.mp4"
            
            cmd = [
                sys.executable, '-m', 'manim',
                'render',
                quality_flag,
                '--format', 'mp4',
                '-o', f"{scene_id}.mp4",
                temp_file.name,
                'GeneratedScene'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.output_dir)
            )
            
            if result.returncode != 0:
                return False, result.stderr or result.stdout
            
            # Find output file
            rendered = self._find_output(scene_id)
            
            if rendered:
                # Move to final location
                if rendered != str(output_path):
                    shutil.move(rendered, output_path)
                logger.info(f"Manim rendered: {output_path}")
                return True, str(output_path)
            
            return False, "Output file not found"
            
        except subprocess.TimeoutExpired:
            return False, "Render timed out"
        except Exception as e:
            return False, str(e)
        finally:
            os.unlink(temp_file.name)
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM response."""
        text = response.strip()
        
        # Remove markdown code blocks if present
        # Pattern 1: ```python ... ```
        match = re.search(r'```(?:python)?\s*\n(.*?)```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        
        # Pattern 2: ``` ... ``` without language
        elif text.startswith('```') and text.endswith('```'):
            text = text[3:-3].strip()
            if text.startswith('python'):
                text = text[6:].strip()
        
        # Ensure it starts with from manim import *
        if not text.startswith('from manim'):
            # Find the start of actual code
            import_match = re.search(r'(from manim import \*.*)', text, re.DOTALL)
            if import_match:
                text = import_match.group(1)
            else:
                # Prepend import if missing
                if 'class GeneratedScene' in text:
                    text = 'from manim import *\n\n' + text
        
        return text
    
    def _find_output(self, scene_id: str) -> Optional[str]:
        """Find rendered video in manim output."""
        # Manim outputs to media/videos/
        media_dir = self.output_dir / 'media' / 'videos'
        
        if media_dir.exists():
            for root, _, files in os.walk(media_dir):
                for f in files:
                    if scene_id in f and f.endswith('.mp4'):
                        return os.path.join(root, f)
        
        # Also check direct output
        direct = self.output_dir / f"{scene_id}.mp4"
        if direct.exists():
            return str(direct)
        
        return None
    
    def _apply_template(self, template_name: str, scene: SceneSpec) -> Optional[str]:
        """Apply pre-built template with scene data."""
        template = MANIM_TEMPLATES.get(template_name)
        if not template:
            return None
        
        # Extract parameters from scene
        params = {}
        if scene.content:
            try:
                import json
                params = json.loads(scene.content)
            except:
                pass
        
        # Default params
        params.setdefault('title', scene.title or 'Animation')
        params.setdefault('values', [1, 2, 3, 4, 5])
        params.setdefault('highlight_indices', [2])
        params.setdefault('target', 3)
        
        try:
            code = template.code_template.format(**params)
            return code
        except Exception as e:
            logger.error(f"Template application failed: {e}")
            return None
    
    async def render_all(self, scenes: list) -> dict:
        """Render all Manim scenes."""
        results = {}
        
        for scene in scenes:
            if scene.visual_type.value == "animated":
                path = await self.generate(scene)
                if path:
                    results[scene.scene_id] = path
        
        return results


def get_manim_generator(
    output_dir: str = "./output/manim",
    config: Optional[VideoConfig] = None
) -> ManimGenerator:
    """Factory for Manim generator."""
    return ManimGenerator(output_dir, config)

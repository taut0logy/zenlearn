"""
Scene Planner Agent.

Plans visual scenes for each script segment.
Decides between static slides, Manim animations, and code walkthroughs.
"""

from typing import List, Optional
import json

from content_gen_engine.video_gen.schemas.video_types import (
    VideoScript, SceneSpec, ScenePlan, SceneType, VisualType, VideoConfig
)
from services.gemini_service import get_gemini_service, GenerationConfig
from utils.logger import logger


SCENE_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "segment_id": {"type": "string"},
                    "scene_type": {"type": "string", "enum": ["title", "content", "code", "manim", "diagram", "summary"]},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "visual_type": {"type": "string", "enum": ["static", "animated", "code_walk"]},
                    "visual_description": {"type": "string"},
                    "manim_description": {"type": "string"},
                    "code": {"type": "string"},
                    "code_language": {"type": "string"},
                    "duration": {"type": "number"},
                    "transition_in": {"type": "string"},
                    "transition_out": {"type": "string"}
                },
                "required": ["scene_id", "segment_id", "scene_type", "duration"]
            }
        }
    },
    "required": ["scenes"]
}


class ScenePlannerAgent:
    """
    Plans visual scenes for video script.
    
    Determines:
    - Scene type (title, content, code, manim, diagram)
    - Visual rendering method
    - Manim animation requirements
    - Transitions between scenes
    """
    
    SYSTEM_PROMPT = """You are a visual director for educational videos.
Your job is to plan engaging visuals that complement narration.
Choose the right visual type for each concept:
- Use MANIM for: algorithms, data structures, mathematical concepts, step-by-step processes
- Use CODE for: showing source code, syntax explanations, debugging
- Use STATIC slides for: definitions, bullet points, simple concepts
- Use DIAGRAMS for: architecture, relationships, comparisons"""

    PLANNING_PROMPT = '''Plan visual scenes for this video script.

<script>
Title: {title}
Hook: {hook}

Segments:
{segments_text}
</script>

<instructions>
For each segment, plan a visual scene:

1. SCENE TYPES:
   - "title": Opening/section title cards
   - "content": Explanatory slides with text/diagrams
   - "code": Code display with syntax highlighting
   - "manim": Animated mathematical/algorithmic visualization
   - "diagram": Static diagram (flowchart, architecture)
   - "summary": Recap/conclusion visuals

2. USE MANIM ANIMATIONS FOR:
   - Algorithm step-by-step (sorting, searching, traversal)
   - Data structure operations (insert, delete, rebalance)
   - Mathematical concepts (graphs, functions, geometry)
   - Process flows that benefit from animation

3. For MANIM scenes, provide manim_description explaining:
   - What to animate
   - Step-by-step what should happen
   - Any specific visual elements

4. Match scene duration to segment duration

Return scenes matching each segment.
</instructions>'''

    def __init__(self, config: Optional[VideoConfig] = None):
        self.config = config or VideoConfig()
        self.llm = get_gemini_service("pro")
    
    async def plan(self, script: VideoScript) -> ScenePlan:
        """
        Plan scenes for video script.
        
        Args:
            script: Generated video script
            
        Returns:
            ScenePlan with scene specifications
        """
        # Format segments for prompt
        segments_text = "\n".join([
            f"[{seg.segment_id}] ({seg.section}, {seg.duration_estimate}s)\n"
            f"  Text: {seg.text[:200]}...\n"
            f"  Visual hint: {seg.visual_suggestion or 'none'}"
            for seg in script.segments
        ])
        
        prompt = self.PLANNING_PROMPT.format(
            title=script.title,
            hook=script.hook,
            segments_text=segments_text
        )
        
        try:
            gen_config = GenerationConfig(
                temperature=0.3,
                system_instruction=self.SYSTEM_PROMPT
            )
            result = await self.llm.generate_structured(
                prompt=prompt,
                response_schema=SCENE_PLAN_SCHEMA,
                config=gen_config
            )
            
            scenes = []
            for scene_data in result['scenes']:
                scene = SceneSpec(
                    scene_id=scene_data['scene_id'],
                    segment_id=scene_data['segment_id'],
                    scene_type=SceneType(scene_data.get('scene_type', 'content')),
                    title=scene_data.get('title'),
                    content=scene_data.get('content'),
                    visual_type=VisualType(scene_data.get('visual_type', 'static')),
                    visual_description=scene_data.get('visual_description'),
                    manim_description=scene_data.get('manim_description'),
                    code=scene_data.get('code'),
                    code_language=scene_data.get('code_language', 'python'),
                    duration=scene_data.get('duration', 5.0),
                    transition_in=scene_data.get('transition_in', 'fade'),
                    transition_out=scene_data.get('transition_out', 'fade')
                )
                scenes.append(scene)
            
            plan = ScenePlan(scenes=scenes)
            logger.info(f"Planned {plan.total_scenes} scenes")
            
            return plan
            
        except Exception as e:
            logger.error(f"Scene planning failed: {e}")
            raise
    
    async def plan_code_walkthrough(
        self,
        code: str,
        script: VideoScript,
        language: str = "python"
    ) -> ScenePlan:
        """
        Plan scenes specifically for code walkthrough.
        
        Creates scenes that progressively reveal and highlight code.
        """
        prompt = f'''Plan visual scenes for a code walkthrough video.

<code>
```{language}
{code}
```
</code>

<script_segments>
{json.dumps([{"id": s.segment_id, "text": s.text[:100]} for s in script.segments], indent=2)}
</script_segments>

<instructions>
Plan scenes that:
1. Start with title card
2. Show full code overview
3. Step through code section by section, highlighting relevant lines
4. For each segment, specify which lines to highlight
5. End with summary

Use scene_type="code" for code scenes.
Include "highlight_lines" as list of line numbers.
</instructions>'''

        result = await self.llm.generate_structured(
            prompt=prompt,
            response_schema=SCENE_PLAN_SCHEMA
        )
        
        scenes = [
            SceneSpec(
                scene_id=s['scene_id'],
                segment_id=s['segment_id'],
                scene_type=SceneType(s.get('scene_type', 'code')),
                title=s.get('title'),
                code=code,  # Full code for all scenes
                code_language=language,
                highlight_lines=s.get('highlight_lines', []),
                visual_description=s.get('visual_description'),
                duration=s.get('duration', 5.0)
            )
            for s in result['scenes']
        ]
        
        return ScenePlan(scenes=scenes)


def get_scene_planner(config: Optional[VideoConfig] = None) -> ScenePlannerAgent:
    """Factory for scene planner."""
    return ScenePlannerAgent(config)

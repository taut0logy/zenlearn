"""
Script Writer Agent.

Generates educational video narration scripts using Gemini.
Uses RAG context + LLM knowledge for comprehensive content.
"""

from typing import Optional
import json

from content_gen_engine.video_gen.schemas.video_types import (
    VideoScript, ScriptSegment, VideoConfig
)
from services.gemini_service import get_gemini_service, GenerationConfig
from utils.logger import logger


# JSON schema for structured output
SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "hook": {"type": "string"},
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "segment_id": {"type": "string"},
                    "text": {"type": "string"},
                    "duration_estimate": {"type": "number"},
                    "section": {"type": "string", "enum": ["introduction", "main", "example", "code", "summary"]},
                    "visual_suggestion": {"type": "string"},
                    "key_concepts": {"type": "array", "items": {"type": "string"}},
                    "emphasis_words": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["segment_id", "text", "duration_estimate", "section"]
            }
        },
        "total_duration_estimate": {"type": "number"},
        "key_takeaways": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["title", "hook", "segments", "total_duration_estimate", "key_takeaways"]
}


class ScriptWriterAgent:
    """
    Generates video narration scripts from topic and context.
    
    Creates:
    - Engaging introduction with hook
    - Structured explanation segments
    - Key concept highlights
    - Summary and takeaways
    
    Uses RAG context + LLM's own knowledge for comprehensive content.
    """
    
    SYSTEM_PROMPT = """You are an expert educational video script writer, 
creating content like 3Blue1Brown or Kurzgesagt. Write scripts that are:
- Engaging and hook viewers immediately
- Clear and educational without being boring
- Conversational yet professional
- Rich with analogies and examples

IMPORTANT: Use BOTH the provided context AND your own knowledge to create 
comprehensive, accurate content. The context provides grounding, but you 
should expand with authoritative information you know."""

    SCRIPT_PROMPT = '''Create a video script explaining this topic.

<topic>
{topic}
</topic>

<context_from_materials>
{context}
</context_from_materials>

<target_duration>
{duration} seconds (approximately {minutes:.1f} minutes)
</target_duration>

<instructions>
Create an educational video script with:

1. OPENING (10-15% of duration):
   - Hook viewer with intriguing question or statement
   - Preview what they'll learn
   - Make it personally relevant

2. MAIN CONTENT (70-80% of duration):
   - Break into 3-5 logical sections
   - Each section: clear explanation + visual suggestion + example
   - Use analogies to explain complex ideas
   - Include both context AND your expert knowledge

3. SUMMARY (10-15% of duration):
   - Recap key points
   - Connect concepts together
   - End with thought-provoking insight

4. STYLE:
   - Speak directly to viewer ("you", "we")
   - Conversational but educational
   - Add [PAUSE] markers for emphasis pauses
   - Mark **important terms** with asterisks
</instructions>

Generate a complete, engaging script:'''

    def __init__(self, config: Optional[VideoConfig] = None):
        self.config = config or VideoConfig()
        self.llm = get_gemini_service("pro")
    
    async def generate(
        self,
        topic: str,
        context: str = "",
        duration_seconds: float = None
    ) -> VideoScript:
        """
        Generate video script.
        
        Args:
            topic: Topic to explain
            context: RAG context from course materials
            duration_seconds: Target duration
            
        Returns:
            VideoScript with segments
        """
        duration = duration_seconds or (self.config.target_duration_minutes * 60)
        
        prompt = self.SCRIPT_PROMPT.format(
            topic=topic,
            context=context or "No specific context provided. Use your knowledge.",
            duration=duration,
            minutes=duration / 60
        )
        
        try:
            # Use structured output with proper config
            gen_config = GenerationConfig(
                temperature=0.7,
                system_instruction=self.SYSTEM_PROMPT
            )
            result = await self.llm.generate_structured(
                prompt=prompt,
                response_schema=SCRIPT_SCHEMA,
                config=gen_config
            )
            
            # Convert to VideoScript
            segments = [
                ScriptSegment(
                    segment_id=seg.get('segment_id', f'seg_{i}'),
                    text=seg['text'],
                    duration_estimate=seg.get('duration_estimate', 10.0),
                    section=seg.get('section', 'main'),
                    visual_suggestion=seg.get('visual_suggestion'),
                    key_concepts=seg.get('key_concepts', []),
                    emphasis_words=seg.get('emphasis_words', [])
                )
                for i, seg in enumerate(result['segments'])
            ]
            
            script = VideoScript(
                title=result['title'],
                hook=result.get('hook', ''),
                segments=segments,
                total_duration_estimate=result.get('total_duration_estimate', duration),
                key_takeaways=result.get('key_takeaways', [])
            )
            
            logger.info(f"Generated script: {script.title} ({len(segments)} segments)")
            return script
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            raise
    
    async def generate_code_script(
        self,
        code: str,
        topic: str,
        language: str = "python",
        duration_seconds: float = None
    ) -> VideoScript:
        """
        Generate script specifically for code walkthrough.
        
        Args:
            code: Source code to explain
            topic: What the code does
            language: Programming language
            duration_seconds: Target duration
        """
        prompt = f'''Create a video script explaining this {language} code.

<code>
```{language}
{code}
```
</code>

<topic>{topic}</topic>

<instructions>
Create a code walkthrough script that:
1. Opens with what problem the code solves
2. Explains the overall structure/approach
3. Walks through key functions one by one
4. Explains tricky parts with analogies
5. Summarizes what we learned

For each segment, include visual_suggestion describing what code to highlight.
Target duration: {duration_seconds or 180} seconds.
</instructions>'''

        result = await self.llm.generate_structured(
            prompt=prompt,
            response_schema=SCRIPT_SCHEMA
        )
        
        segments = [
            ScriptSegment(**{**seg, 'segment_id': seg.get('segment_id', f'seg_{i}')})
            for i, seg in enumerate(result['segments'])
        ]
        
        return VideoScript(
            title=result['title'],
            hook=result.get('hook', ''),
            segments=segments,
            total_duration_estimate=result.get('total_duration_estimate', 180),
            key_takeaways=result.get('key_takeaways', [])
        )


def get_script_writer(config: Optional[VideoConfig] = None) -> ScriptWriterAgent:
    """Factory for script writer."""
    return ScriptWriterAgent(config)

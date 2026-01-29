"""
Content Planner Agent.

Plans the structure of generated learning materials.
"""

from typing import Optional, List, Dict, Any
from services.gemini_service import GeminiService, GenerationConfig, get_gemini_service
from content_gen_engine.schemas.content_tags import ContentPlan, SectionPlan, VisualPlan, DocumentTheme
from utils.logger import logger


class ContentPlanner:
    """
    Plans document structure before generation.
    
    Analyzes the topic and creates a structured plan including:
    - Section breakdown
    - Visual elements needed
    - Code examples to include
    """
    
    PLANNING_PROMPT = '''You are an expert educational content designer. Plan the structure for learning materials on the given topic.

<topic>
{topic}
</topic>

<output_type>
{output_type}
</output_type>

<context>
{context}
</context>

<requirements>
- Target audience: University students
- Include visual elements (images, diagrams) where helpful
- Include code examples for technical topics
- Plan for {num_pages} pages/slides approximately
- Make content engaging and pedagogically sound
</requirements>

Create a detailed content plan. Return JSON:

{{
    "title": "Document title",
    "output_type": "{output_type}",
    "estimated_pages": {num_pages},
    "target_audience": "University students",
    "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
    "sections": [
        {{
            "title": "Section title",
            "section_type": "content|code|summary|exercise",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "visuals_needed": [
                {{
                    "visual_type": "image|diagram",
                    "description": "What it should show"
                }}
            ],
            "code_examples": ["Description of code example if needed"]
        }}
    ],
    "visual_theme": {{
        "primary_color": "#1a365d",
        "secondary_color": "#2c5282",
        "accent_color": "#3182ce",
        "font_family": "Helvetica",
        "style": "modern"
    }}
}}
'''
    
    def __init__(self, llm: Optional[GeminiService] = None):
        """Initialize planner with LLM service."""
        self.llm = llm or get_gemini_service("pro")
    
    async def plan(
        self,
        topic: str,
        output_type: str = "markdown",
        context: Optional[str] = None,
        num_pages: int = 5
    ) -> ContentPlan:
        """
        Generate content plan for a topic.
        
        Args:
            topic: Subject to create content for
            output_type: Target format (markdown, pdf, pptx, lab)
            context: Optional retrieved context
            num_pages: Target number of pages
            
        Returns:
            ContentPlan with structured sections
        """
        prompt = self.PLANNING_PROMPT.format(
            topic=topic,
            output_type=output_type,
            context=context or "No additional context provided.",
            num_pages=num_pages
        )
        
        try:
            result = await self.llm.generate_json(prompt)
            
            # Parse into ContentPlan
            sections = []
            for s in result.get('sections', []):
                visuals = [
                    VisualPlan(
                        visual_type=v.get('visual_type', 'image'),
                        description=v.get('description', '')
                    )
                    for v in s.get('visuals_needed', [])
                ]
                
                sections.append(SectionPlan(
                    title=s.get('title', ''),
                    section_type=s.get('section_type', 'content'),
                    key_points=s.get('key_points', []),
                    visuals_needed=visuals,
                    code_examples=s.get('code_examples', [])
                ))
            
            theme_data = result.get('visual_theme', {})
            theme = DocumentTheme(
                primary_color=theme_data.get('primary_color', '#1a365d'),
                secondary_color=theme_data.get('secondary_color', '#2c5282'),
                accent_color=theme_data.get('accent_color', '#3182ce'),
                font_family=theme_data.get('font_family', 'Helvetica'),
                style=theme_data.get('style', 'modern')
            )
            
            return ContentPlan(
                title=result.get('title', topic),
                output_type=output_type,
                estimated_pages=result.get('estimated_pages', num_pages),
                sections=sections,
                visual_theme=theme,
                target_audience=result.get('target_audience', 'University students'),
                prerequisites=result.get('prerequisites', [])
            )
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            # Return minimal plan
            return ContentPlan(
                title=topic,
                output_type=output_type,
                estimated_pages=num_pages,
                sections=[
                    SectionPlan(
                        title="Introduction",
                        section_type="content",
                        key_points=[f"Overview of {topic}"]
                    ),
                    SectionPlan(
                        title="Main Content",
                        section_type="content",
                        key_points=["Key concepts", "Examples"]
                    ),
                    SectionPlan(
                        title="Summary",
                        section_type="summary",
                        key_points=["Key takeaways"]
                    )
                ]
            )


# Factory
def get_content_planner() -> ContentPlanner:
    """Get content planner instance."""
    return ContentPlanner()

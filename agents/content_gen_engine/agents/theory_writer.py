"""
Theory Writer Agent.

Generates structured theory content (notes, explanations) using XML tags.
"""

from typing import Optional
import json

from services.gemini_service import GeminiService, GenerationConfig, get_gemini_service
from content_gen_engine.schemas.content_tags import ContentPlan, DocumentSpec
from content_gen_engine.parsers.structured_parser import StructuredContentParser, ParsedDocument
from utils.logger import logger


class TheoryWriter:
    """
    Generates theory/educational content with structured tags.
    
    Produces XML-tagged content that can be parsed and rendered
    into Markdown, PDF, or PPTX.
    """
    
    CONTENT_PROMPT = '''You are an expert educational content creator. Generate learning materials using structured XML tags.

<plan>
{plan}
</plan>

<context>
{context}
</context>

<rules>
1. Generate content following the plan structure
2. Use ONLY information from context if provided, otherwise use your knowledge
3. Keep language clear, educational, and engaging
4. Include practical examples
5. For technical topics, include code examples
6. IMPORTANT: All lists MUST have at least 3-5 items with actual content
7. NEVER create empty list items - each <item> must have meaningful text
8. For "Key Takeaways" sections, provide concrete, actionable insights
</rules>

<output_format>
Generate content using these XML tags:

<document type="{output_type}" title="Document Title">

<page number="1" type="title">
<title>Main Title</title>
<subtitle>Subtitle if needed</subtitle>
</page>

<page number="2" type="content">
<heading level="1">Section Heading</heading>
<paragraph>Content text here...</paragraph>

<img prompt="detailed description for AI image generation" 
     alt="accessibility text" 
     position="center" 
     width="80%"/>

<mermaid type="flowchart" caption="Optional caption">
A[Start] --> B[Process]
B --> C[End]
</mermaid>

NOTE: For mermaid diagrams:
- DO NOT include type declarations (flowchart TD, sequenceDiagram, etc.)
- Only include the diagram content/nodes
- The type attribute handles the diagram type

<code language="python" title="Example">
def example():
    return "Hello"
</code>

<callout type="info|warning|tip">
Important information here
</callout>

<list type="bullet">
<item>Point 1</item>
<item>Point 2</item>
</list>
</page>

<page number="N" type="summary">
<heading level="1">Key Takeaways</heading>
<list type="bullet">
<item>Takeaway 1</item>
<item>Takeaway 2</item>
</list>
</page>

</document>
</output_format>

Generate the complete document:
'''
    
    def __init__(self, llm: Optional[GeminiService] = None):
        """Initialize writer with LLM service."""
        self.llm = llm or get_gemini_service("pro")
        self.parser = StructuredContentParser()
    
    async def generate(
        self,
        plan: ContentPlan,
        context: Optional[str] = None
    ) -> ParsedDocument:
        """
        Generate structured content from plan.
        
        Args:
            plan: Content plan from ContentPlanner
            context: Optional retrieved context
            
        Returns:
            ParsedDocument with all content elements
        """
        # Format plan for prompt
        plan_dict = {
            "title": plan.title,
            "output_type": plan.output_type,
            "sections": [
                {
                    "title": s.title,
                    "type": s.section_type,
                    "key_points": s.key_points,
                    "visuals": [{"type": v.visual_type, "desc": v.description} for v in s.visuals_needed],
                    "code_examples": s.code_examples
                }
                for s in plan.sections
            ]
        }
        
        prompt = self.CONTENT_PROMPT.format(
            plan=json.dumps(plan_dict, indent=2),
            context=context or "Use your knowledge to generate comprehensive content.",
            output_type=plan.output_type
        )
        
        try:
            config = GenerationConfig(
                temperature=0.4,  # Balanced creativity/accuracy
                max_output_tokens=8192
            )
            
            raw_content = await self.llm.generate(prompt, config)
            
            # Parse the generated content
            document = self.parser.parse(raw_content)
            
            # Apply plan metadata
            document.title = plan.title
            document.document_type = plan.output_type
            
            logger.info(f"Generated document with {len(document.pages)} pages")
            return document
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise
    
    async def generate_raw(
        self,
        plan: ContentPlan,
        context: Optional[str] = None
    ) -> str:
        """
        Generate raw XML content without parsing.
        
        Useful for debugging or custom processing.
        """
        plan_dict = {
            "title": plan.title,
            "output_type": plan.output_type,
            "sections": [
                {
                    "title": s.title,
                    "type": s.section_type,
                    "key_points": s.key_points
                }
                for s in plan.sections
            ]
        }
        
        prompt = self.CONTENT_PROMPT.format(
            plan=json.dumps(plan_dict, indent=2),
            context=context or "Use your knowledge.",
            output_type=plan.output_type
        )
        
        config = GenerationConfig(temperature=0.4, max_output_tokens=8192)
        return await self.llm.generate(prompt, config)


# Factory
def get_theory_writer() -> TheoryWriter:
    """Get theory writer instance."""
    return TheoryWriter()

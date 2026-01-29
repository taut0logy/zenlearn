"""
Content Generation Tool.

Wraps the Content Generation Pipeline for use by the Chat Agent.
Allows generation of theory, labs, images, and diagrams based on user requests.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Literal
from langchain_core.tools import tool

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from content_gen_engine.pipeline import get_content_pipeline, PipelineConfig
from config.settings import settings
from utils.logger import logger

# Singleton instance
_pipeline_instance = None


def _get_pipeline() -> object:
    """Get or create the content pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        # Output to contents/generated so it's served by FastAPI
        output_dir = os.path.join(settings.BASE_DIR, "contents", "generated")

        config = PipelineConfig(
            output_dir=output_dir,
            generate_images=True,
            generate_diagrams=True,
            validate_code=True,
            num_pages=3,
        )
        _pipeline_instance = get_content_pipeline(config)
    return _pipeline_instance


@tool
async def generate_learning_content(
    topic: str,
    content_type: Literal["theory", "lab"] = "theory",
    context: Optional[str] = None,
    generate_images: bool = True,
    generate_diagrams: bool = True,
) -> str:
    """
    Generate comprehensive learning content like tutorials, guides, or labs.

    Use this tool when the user explicitly asks to generate content, create a guide,
    make a lab, or uses commands like /content, /lab, /pdf, /image, /diagram.

    CRITICAL: You MUST perform a `course_materials_search` FIRST to get relevant
    context from the uploaded course materials. Process that search result and
    pass it as the `context` argument to this tool.

    Args:
        topic: The specific topic to generate content for (e.g. "Binary Search Guide")
        content_type: "theory" for guides/tutorials, "lab" for coding exercises
        context: RELEVANT background information retrieved from course materials search.
                 Do not pass "None" if you can find course material.
        generate_images: Whether to generate AI images (default: True)
        generate_diagrams: Whether to generate Mermaid diagrams (default: True)

    Returns:
        A formatted string with links to the generated content.
    """
    try:
        pipeline = _get_pipeline()

        # Override config if needed (not thread safe but okay for single agent instance)
        pipeline.config.generate_images = generate_images
        pipeline.config.generate_diagrams = generate_diagrams

        logger.info(f"[ContentGen] Generating {content_type} for: {topic}")

        # Request PDF output
        result = await pipeline.generate(
            topic=topic, content_type=content_type, context=context, output_type="pdf"
        )

        if result.success:
            # Convert local path to served URL
            # Path is like .../contents/generated/file.pdf
            # URL should be http://host:port/contents/generated/file.pdf

            output_path = result.output_path.replace("\\", "/")

            if "/contents/" in output_path:
                relative_path = output_path.split("/contents/")[-1]
                # Use localhost if 0.0.0.0 to be safer for local dev
                host = settings.HOST if settings.HOST != "0.0.0.0" else "localhost"
                base_url = f"http://{host}:{settings.PORT}"
                url = f"{base_url}/contents/{relative_path}"

                # Check for assets (images/diagrams)
                assets_info = ""
                if result.assets:
                    assets_info = f"\n\nGenerated {len(result.assets)} visual assets (images/diagrams) embedded in the PDF."

                return (
                    f"✅ **Content Generated Successfully!**\n\n"
                    f"**Title:** {result.plan.title if result.plan else result.lab.title if result.lab else topic}\n"
                    f"**Action:** [📄 Download PDF]({url})\n"
                    f"{assets_info}\n\n"
                    f"Click the link above to download the rendered content."
                )
            else:
                return f"Content generated at: {result.output_path}"
        else:
            return f"❌ Content generation failed: {result.error}"

    except Exception as e:
        logger.error(f"[ContentGen] Tool error: {e}")
        return f"Error executing content generation: {str(e)}"


# Export
content_gen_tool = generate_learning_content

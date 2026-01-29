"""
Content Generation Engine.

AI-powered learning material generation with validation.
"""

from content_gen_engine.pipeline import (
    ContentPipeline,
    PipelineConfig,
    GenerationResult,
    get_content_pipeline,
)

from content_gen_engine.agents import (
    ContentPlanner,
    TheoryWriter,
    CodeWriter,
    get_content_planner,
    get_theory_writer,
    get_code_writer,
)

from content_gen_engine.generators import (
    MarkdownGenerator,
    DiagramGenerator,
    get_markdown_generator,
    get_diagram_generator,
)

from content_gen_engine.validators import (
    SyntaxChecker,
    CodeExecutor,
    ContentValidator,
    ValidationResult,
)

__all__ = [
    # Pipeline
    "ContentPipeline",
    "PipelineConfig",
    "GenerationResult",
    "get_content_pipeline",
    
    # Agents
    "ContentPlanner",
    "TheoryWriter",
    "CodeWriter",
    "get_content_planner",
    "get_theory_writer",
    "get_code_writer",
    
    # Generators
    "MarkdownGenerator",
    "DiagramGenerator",
    "get_markdown_generator",
    "get_diagram_generator",
    
    # Validators
    "SyntaxChecker",
    "CodeExecutor",
    "ContentValidator",
    "ValidationResult",
]

"""
Content Generation Pipeline.

Orchestrates the full content generation flow.
"""

from typing import Optional, Literal, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from content_gen_engine.agents.content_planner import ContentPlanner, get_content_planner
from content_gen_engine.agents.theory_writer import TheoryWriter, get_theory_writer
from content_gen_engine.agents.code_writer import CodeWriter, get_code_writer
from content_gen_engine.generators.markdown_generator import MarkdownGenerator, get_markdown_generator
from content_gen_engine.generators.diagram_generator import DiagramGenerator, get_diagram_generator
from content_gen_engine.validators.code_validator import (
    SyntaxChecker, CodeExecutor, ContentValidator,
    get_syntax_checker, get_code_executor, get_content_validator
)
from content_gen_engine.parsers.structured_parser import ParsedDocument
from content_gen_engine.schemas.content_tags import ContentPlan, LabSpec
from services.image_gen_service import ImageGenService, get_image_gen_service
from utils.logger import logger


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    output_dir: str = "./output"
    generate_images: bool = True
    generate_diagrams: bool = True
    validate_code: bool = True
    validate_content: bool = False  # Requires RAG context
    num_pages: int = 5


@dataclass  
class GenerationResult:
    """Result of content generation."""
    success: bool
    output_path: Optional[str] = None
    output_type: str = "markdown"
    plan: Optional[ContentPlan] = None
    document: Optional[ParsedDocument] = None
    lab: Optional[LabSpec] = None
    assets: Dict[str, str] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class ContentPipeline:
    """
    Main content generation pipeline.
    
    Orchestrates:
    1. Planning (structure, visuals, code)
    2. Writing (theory or lab content)
    3. Asset generation (images, diagrams)
    4. Validation (syntax, tests, grounding)
    5. Output generation (markdown, PDF, PPTX)
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        
        # Initialize components
        self.planner = get_content_planner()
        self.theory_writer = get_theory_writer()
        self.code_writer = get_code_writer()
        self.markdown_gen = get_markdown_generator(self.config.output_dir)
        self.diagram_gen = get_diagram_generator(f"{self.config.output_dir}/diagrams")
        
        self.syntax_checker = get_syntax_checker()
        self.code_executor = get_code_executor()
        
        # Image generation (optional)
        try:
            self.image_gen = get_image_gen_service(f"{self.config.output_dir}/images")
        except Exception as e:
            logger.warning(f"Image generation unavailable: {e}")
            self.image_gen = None
        
        # Output directory
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
    
    async def generate_theory(
        self,
        topic: str,
        output_type: Literal["markdown", "pdf", "pptx"] = "markdown",
        context: Optional[str] = None,
        num_pages: int = None
    ) -> GenerationResult:
        """
        Generate theory learning materials.
        
        Args:
            topic: Subject to create content for
            output_type: Output format
            context: Optional RAG context
            num_pages: Number of pages
            
        Returns:
            GenerationResult
        """
        try:
            num_pages = num_pages or self.config.num_pages
            
            # 1. Plan
            logger.info(f"Planning content for: {topic}")
            plan = await self.planner.plan(
                topic=topic,
                output_type=output_type,
                context=context,
                num_pages=num_pages
            )
            
            # 2. Generate content
            logger.info(f"Generating content: {len(plan.sections)} sections")
            document = await self.theory_writer.generate(plan, context)
            
            # 3. Generate assets
            assets = {}
            
            # Diagrams
            if self.config.generate_diagrams:
                all_diagrams = []
                for page in document.pages:
                    all_diagrams.extend(page.content.diagrams)
                
                if all_diagrams:
                    logger.info(f"Rendering {len(all_diagrams)} diagrams")
                    diagram_paths = await self.diagram_gen.render_batch(all_diagrams)
                    assets.update({k: v for k, v in diagram_paths.items() if v})
            
            # Images
            if self.config.generate_images and self.image_gen:
                all_images = []
                for page in document.pages:
                    for img in page.content.images:
                        all_images.append({"id": img.id, "prompt": img.prompt})
                
                if all_images:
                    logger.info(f"Generating {len(all_images)} images")
                    try:
                        image_paths = await self.image_gen.generate_batch(all_images)
                        assets.update({k: v for k, v in image_paths.items() if v})
                    except Exception as e:
                        logger.warning(f"Image generation failed: {e}")
            
            # 4. Generate output
            if output_type == "markdown":
                output_path = self.markdown_gen.save(document, image_paths=assets)
            else:
                # For PDF/PPTX, generate markdown first
                output_path = self.markdown_gen.save(document, image_paths=assets)
                # TODO: Add PDF/PPTX exporters
                logger.info(f"Generated markdown at {output_path}. PDF/PPTX export coming soon.")
            
            return GenerationResult(
                success=True,
                output_path=output_path,
                output_type=output_type,
                plan=plan,
                document=document,
                assets=assets
            )
            
        except Exception as e:
            logger.error(f"Theory generation failed: {e}")
            return GenerationResult(success=False, error=str(e))
    
    async def generate_lab(
        self,
        topic: str,
        language: str = "python",
        context: Optional[str] = None
    ) -> GenerationResult:
        """
        Generate lab/code learning materials.
        
        Args:
            topic: Programming topic
            language: Target language
            context: Optional RAG context
            
        Returns:
            GenerationResult with lab and validation
        """
        try:
            # 1. Generate lab
            logger.info(f"Generating lab: {topic} ({language})")
            lab = await self.code_writer.generate_lab(
                topic=topic,
                language=language,
                context=context
            )
            
            validation = {}
            
            # 2. Validate solution code
            if self.config.validate_code and lab.solution_code:
                logger.info("Validating solution code")
                
                # Syntax check
                syntax_result = self.syntax_checker.check(
                    lab.solution_code.code,
                    language
                )
                validation['syntax'] = {
                    'is_valid': syntax_result.is_valid,
                    'error': syntax_result.error_message
                }
                
                # Run tests if syntax valid
                if syntax_result.is_valid and lab.test_cases:
                    logger.info(f"Running {len(lab.test_cases)} test cases")
                    test_result = self.code_executor.run_tests(
                        lab.solution_code.code,
                        lab.test_cases,
                        language
                    )
                    validation['tests'] = {
                        'passed': test_result.passed_tests,
                        'failed': test_result.failed_tests,
                        'results': test_result.test_results
                    }
            
            # 3. Generate markdown output
            output_path = self._generate_lab_markdown(lab)
            
            return GenerationResult(
                success=True,
                output_path=output_path,
                output_type="lab",
                lab=lab,
                validation=validation
            )
            
        except Exception as e:
            logger.error(f"Lab generation failed: {e}")
            return GenerationResult(success=False, error=str(e))
    
    def _generate_lab_markdown(self, lab: LabSpec) -> str:
        """Generate markdown for lab."""
        lines = [
            f"# {lab.title}",
            "",
            f"**Difficulty:** {lab.difficulty}",
            "",
            "## Description",
            lab.description,
            ""
        ]
        
        if lab.objectives:
            lines.append("## Learning Objectives")
            for obj in lab.objectives:
                lines.append(f"- {obj}")
            lines.append("")
        
        if lab.starter_code:
            lines.append("## Starter Code")
            lines.append(f"```{lab.starter_code.language}")
            lines.append(lab.starter_code.code)
            lines.append("```")
            lines.append("")
        
        if lab.test_cases:
            visible = [tc for tc in lab.test_cases if not tc.is_hidden]
            if visible:
                lines.append("## Test Cases")
                for i, tc in enumerate(visible, 1):
                    lines.append(f"### Test {i}")
                    lines.append(f"**Input:**\n```\n{tc.input}\n```")
                    lines.append(f"**Expected Output:**\n```\n{tc.expected_output}\n```")
                    if tc.description:
                        lines.append(f"*{tc.description}*")
                    lines.append("")
        
        if lab.hints:
            lines.append("## Hints")
            for hint in lab.hints:
                lines.append(f"- 💡 {hint}")
            lines.append("")
        
        # Solution (collapsed)
        if lab.solution_code:
            lines.append("<details>")
            lines.append("<summary>📖 View Solution</summary>")
            lines.append("")
            lines.append(f"```{lab.solution_code.language}")
            lines.append(lab.solution_code.code)
            lines.append("```")
            lines.append("</details>")
        
        content = "\n".join(lines)
        
        # Save
        slug = lab.title.lower().replace(' ', '-')[:30]
        output_path = Path(self.config.output_dir) / f"lab-{slug}.md"
        output_path.write_text(content, encoding='utf-8')
        
        logger.info(f"Saved lab: {output_path}")
        return str(output_path)
    
    async def generate(
        self,
        topic: str,
        content_type: Literal["theory", "lab"] = "theory",
        **kwargs
    ) -> GenerationResult:
        """
        Unified generation interface.
        
        Routes to theory or lab generation based on type.
        """
        if content_type == "lab":
            return await self.generate_lab(topic, **kwargs)
        else:
            return await self.generate_theory(topic, **kwargs)


# Factory
def get_content_pipeline(config: Optional[PipelineConfig] = None) -> ContentPipeline:
    """Get content pipeline instance."""
    return ContentPipeline(config)

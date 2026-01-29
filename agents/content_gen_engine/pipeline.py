"""
Content Generation Pipeline.

Orchestrates the full content generation flow.
"""

from typing import Optional, Literal, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import os

from content_gen_engine.agents.content_planner import (
    ContentPlanner,
    get_content_planner,
)
from content_gen_engine.agents.theory_writer import TheoryWriter, get_theory_writer
from content_gen_engine.agents.code_writer import CodeWriter, get_code_writer
from content_gen_engine.generators.markdown_generator import (
    MarkdownGenerator,
    get_markdown_generator,
)
from content_gen_engine.generators.diagram_generator import (
    DiagramGenerator,
    get_diagram_generator,
)
from content_gen_engine.validators.code_validator import (
    SyntaxChecker,
    CodeExecutor,
    ContentValidator,
    get_syntax_checker,
    get_code_executor,
    get_content_validator,
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
        num_pages: int = None,
        progress_callback: Optional[Any] = None,
    ) -> GenerationResult:
        """
        Generate theory learning materials.

        Args:
            topic: Subject to create content for
            output_type: Output format
            context: Optional RAG context
            num_pages: Number of pages
            progress_callback: Async callback for status updates

        Returns:
            GenerationResult
        """
        try:
            num_pages = num_pages or self.config.num_pages

            # 1. Plan
            logger.info(f"Planning content for: {topic}")
            if progress_callback:
                await progress_callback(f"Planning content structure for '{topic}'...")

            plan = await self.planner.plan(
                topic=topic,
                output_type=output_type,
                context=context,
                num_pages=num_pages,
            )

            # 2. Generate content
            logger.info(f"Generating content: {len(plan.sections)} sections")
            if progress_callback:
                await progress_callback(
                    f"Drafting content for {len(plan.sections)} sections..."
                )

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
                    if progress_callback:
                        await progress_callback(
                            f"Generating {len(all_diagrams)} Mermaid diagrams..."
                        )

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
                    if progress_callback:
                        await progress_callback(
                            f"Creating {len(all_images)} AI illustrations..."
                        )

                    try:
                        image_paths = await self.image_gen.generate_batch(all_images)
                        assets.update({k: v for k, v in image_paths.items() if v})
                    except Exception as e:
                        logger.warning(f"Image generation failed: {e}")

            # 4. Generate output
            if progress_callback:
                await progress_callback("Finalizing document...")

            md_path = self.markdown_gen.save(document, image_paths=assets)
            output_path = md_path

            if output_type == "pdf":
                if progress_callback:
                    await progress_callback("Converting to PDF format...")

                pdf_path = md_path.replace(".md", ".pdf")
                markdown_content = Path(md_path).read_text(encoding="utf-8")

                # Base URL for images (output dir)
                base_url = str(Path(self.config.output_dir).absolute())

                success = self._convert_to_pdf(markdown_content, pdf_path, base_url)
                if success:
                    output_path = pdf_path
                    logger.info(f"Generated PDF at {output_path}")
                else:
                    logger.warning("PDF generation failed, falling back to Markdown")

            if progress_callback:
                await progress_callback("Generation complete!")

            return GenerationResult(
                success=True,
                output_path=output_path,
                output_type=output_type,
                plan=plan,
                document=document,
                assets=assets,
            )

        except Exception as e:
            logger.error(f"Theory generation failed: {e}")
            if progress_callback:
                await progress_callback(f"Error: {e}")
            return GenerationResult(success=False, error=str(e))

    def _convert_to_pdf(
        self, markdown_content: str, output_path: str, base_url: str = ""
    ) -> bool:
        """Convert Markdown to PDF."""
        try:
            import markdown
            from xhtml2pdf import pisa

            # Extensions
            extensions = ["extra", "codehilite", "tables", "fenced_code"]

            # Convert MD to HTML
            html_body = markdown.markdown(markdown_content, extensions=extensions)

            # Add styling
            html_content = f"""
            <html>
            <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{ 
                    font-family: Helvetica, Arial, sans-serif; 
                    font-size: 11pt; 
                    line-height: 1.5;
                    color: #333;
                }}
                h1 {{ font-size: 24pt; color: #2C3E50; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                h2 {{ font-size: 18pt; color: #34495E; margin-top: 25px; border-bottom: 1px solid #eee; }}
                h3 {{ font-size: 14pt; color: #7F8C8D; margin-top: 20px; }}
                pre {{ 
                    background-color: #f8f9fa; 
                    padding: 15px; 
                    border: 1px solid #e9ecef; 
                    border-radius: 5px;
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 9pt;
                    white-space: pre-wrap;
                }}
                code {{ 
                    background-color: #f8f9fa; 
                    padding: 2px 4px; 
                    border-radius: 3px;
                    font-family: 'Courier New', Courier, monospace;
                }}
                blockquote {{
                    border-left: 4px solid #3498DB;
                    margin: 0;
                    padding-left: 15px;
                    color: #555;
                    background-color: #ecf0f1;
                    padding: 10px;
                }}
                img {{ 
                    max-width: 100%; 
                    height: auto; 
                    margin: 20px 0; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
            </head>
            <body>
            {html_body}
            </body>
            </html>
            """

            with open(output_path, "wb") as f:
                pisa_status = pisa.CreatePDF(
                    html_content,
                    dest=f,
                    link_callback=lambda uri, rel: os.path.join(base_url, uri)
                    if not uri.startswith("http")
                    else uri,
                )

            if pisa_status.err:
                logger.error(f"PDF generation error: {pisa_status.err}")
                return False
            return True

        except ImportError:
            logger.error("markdown or xhtml2pdf not installed")
            return False
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def generate_lab(
        self,
        topic: str,
        language: str = "python",
        context: Optional[str] = None,
        progress_callback: Optional[Any] = None,
    ) -> GenerationResult:
        """
        Generate lab/code learning materials.

        Args:
            topic: Programming topic
            language: Target language
            context: Optional RAG context
            progress_callback: Async callback for status updates

        Returns:
            GenerationResult with lab and validation
        """
        try:
            # 1. Generate lab
            logger.info(f"Generating lab: {topic} ({language})")
            if progress_callback:
                await progress_callback(f"Designing coding lab for '{topic}'...")

            lab = await self.code_writer.generate_lab(
                topic=topic, language=language, context=context
            )

            validation = {}

            # 2. Validate solution code
            if self.config.validate_code and lab.solution_code:
                logger.info("Validating solution code")
                if progress_callback:
                    await progress_callback("Validating solution code...")

                # Syntax check
                syntax_result = self.syntax_checker.check(
                    lab.solution_code.code, language
                )
                validation["syntax"] = {
                    "is_valid": syntax_result.is_valid,
                    "error": syntax_result.error_message,
                }

                # Run tests if syntax valid
                if syntax_result.is_valid and lab.test_cases:
                    logger.info(f"Running {len(lab.test_cases)} test cases")
                    if progress_callback:
                        await progress_callback(
                            f"Running {len(lab.test_cases)} test cases..."
                        )

                    test_result = self.code_executor.run_tests(
                        lab.solution_code.code, lab.test_cases, language
                    )
                    validation["tests"] = {
                        "passed": test_result.passed_tests,
                        "failed": test_result.failed_tests,
                        "results": test_result.test_results,
                    }

            # 3. Generate markdown output
            if progress_callback:
                await progress_callback("Saving lab files...")

            output_path = self._generate_lab_markdown(lab)

            if progress_callback:
                await progress_callback("Lab generation complete!")

            return GenerationResult(
                success=True,
                output_path=output_path,
                output_type="lab",
                lab=lab,
                validation=validation,
            )

        except Exception as e:
            logger.error(f"Lab generation failed: {e}")
            if progress_callback:
                await progress_callback(f"Error: {e}")
            return GenerationResult(success=False, error=str(e))

    # ... _generate_lab_markdown ...

    async def generate(
        self, topic: str, content_type: Literal["theory", "lab"] = "theory", **kwargs
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

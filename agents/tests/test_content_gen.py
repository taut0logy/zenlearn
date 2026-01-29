"""
Test Content Generation Pipeline.

Tests for the content generation engine including assets.
"""

import asyncio
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_gen_engine.pipeline import get_content_pipeline, PipelineConfig
from content_gen_engine.agents import get_content_planner, get_code_writer
from content_gen_engine.generators import get_diagram_generator, get_markdown_generator
from content_gen_engine.validators import get_syntax_checker
from content_gen_engine.parsers import ParsedMermaid


async def test_content_planner():
    """Test content planning."""
    print("\n=== Testing Content Planner ===")
    
    planner = get_content_planner()
    
    plan = await planner.plan(
        topic="Binary Search Algorithm",
        output_type="markdown",
        num_pages=3
    )
    
    print(f"✓ Title: {plan.title}")
    print(f"✓ Sections: {len(plan.sections)}")
    for s in plan.sections:
        print(f"  - {s.title} ({s.section_type})")
        if s.visuals_needed:
            print(f"    Visuals: {[v.visual_type for v in s.visuals_needed]}")
    print(f"✓ Theme style: {plan.visual_theme.style}")
    
    return plan


async def test_lab_generation():
    """Test lab code generation."""
    print("\n=== Testing Lab Generation ===")
    
    code_writer = get_code_writer()
    
    lab = await code_writer.generate_lab(
        topic="Implement a function to reverse a string",
        language="python",
        difficulty="easy"
    )
    
    print(f"✓ Title: {lab.title}")
    print(f"✓ Difficulty: {lab.difficulty}")
    print(f"✓ Test cases: {len(lab.test_cases)}")
    
    if lab.solution_code:
        print(f"\n--- Solution Preview ---")
        print(lab.solution_code.code[:300] + "...")
    
    # Validate solution
    if lab.solution_code:
        checker = get_syntax_checker()
        result = checker.check(lab.solution_code.code, "python")
        print(f"\n✓ Syntax valid: {result.is_valid}")
        if not result.is_valid:
            print(f"  Error: {result.error_message}")
    
    return lab


async def test_diagram_generation():
    """Test Mermaid diagram generation."""
    print("\n=== Testing Diagram Generation ===")
    
    diagram_gen = get_diagram_generator("./test_output/diagrams")
    
    # Test flowchart
    flowchart = ParsedMermaid(
        id="test_flowchart",
        diagram_type="flowchart",
        code="""
flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process]
    B -->|No| D[End]
    C --> D
""",
        caption="Test Flowchart"
    )
    
    # Test sequence diagram
    sequence = ParsedMermaid(
        id="test_sequence",
        diagram_type="sequence",
        code="""
sequenceDiagram
    User->>Server: Request
    Server->>Database: Query
    Database-->>Server: Result
    Server-->>User: Response
""",
        caption="Test Sequence"
    )
    
    # Render diagrams
    result1 = await diagram_gen.render(flowchart)
    print(f"✓ Flowchart: {result1 or 'CLI not available (mermaid code saved)'}")
    
    result2 = await diagram_gen.render(sequence)
    print(f"✓ Sequence: {result2 or 'CLI not available (mermaid code saved)'}")
    
    # Get code without rendering
    codes = diagram_gen.get_diagram_code([flowchart, sequence])
    print(f"✓ Got diagram codes: {list(codes.keys())}")
    
    return result1, result2


async def test_image_generation():
    """Test image generation with Gemini Imagen."""
    print("\n=== Testing Image Generation ===")
    
    try:
        from services.image_gen_service import get_image_gen_service
        
        image_gen = get_image_gen_service("./test_output/images")
        
        # Generate a simple educational image
        path = await image_gen.generate(
            prompt="Simple diagram showing binary search dividing an array in half",
            filename="binary_search_concept"
        )
        
        print(f"✓ Image generated: {path}")
        return path
        
    except Exception as e:
        print(f"⚠ Image generation failed: {e}")
        print("  (This may be due to API quota or configuration)")
        return None


async def test_full_pipeline():
    """Test full pipeline generation."""
    print("\n=== Testing Full Pipeline ===")
    
    config = PipelineConfig(
        output_dir="./test_output",
        generate_images=False,  # Skip for quick test (set True to test)
        generate_diagrams=True,
        num_pages=3
    )
    
    pipeline = get_content_pipeline(config)
    
    # Test theory generation
    print("\n--- Theory Generation ---")
    result = await pipeline.generate_theory(
        topic="Introduction to Recursion",
        output_type="markdown"
    )
    
    print(f"✓ Success: {result.success}")
    if result.success:
        print(f"✓ Output: {result.output_path}")
        print(f"✓ Pages: {len(result.document.pages) if result.document else 'N/A'}")
        print(f"✓ Assets: {len(result.assets)}")
    else:
        print(f"✗ Error: {result.error}")
    
    return result


async def test_full_pipeline_with_images():
    """Test full pipeline with image generation enabled."""
    print("\n=== Testing Full Pipeline (with Images) ===")
    
    config = PipelineConfig(
        output_dir="./test_output",
        generate_images=True,
        generate_diagrams=True,
        num_pages=2  # Shorter for testing
    )
    
    pipeline = get_content_pipeline(config)
    
    result = await pipeline.generate_theory(
        topic="How Binary Trees Work",
        output_type="markdown"
    )
    
    print(f"✓ Success: {result.success}")
    if result.success:
        print(f"✓ Output: {result.output_path}")
        print(f"✓ Pages: {len(result.document.pages) if result.document else 'N/A'}")
        print(f"✓ Images generated: {sum(1 for v in result.assets.values() if v and 'img' in str(v))}")
        print(f"✓ Diagrams generated: {sum(1 for v in result.assets.values() if v and 'diagram' in str(v))}")
    else:
        print(f"✗ Error: {result.error}")
    
    return result


async def test_syntax_checker():
    """Test syntax checker."""
    print("\n=== Testing Syntax Checker ===")
    
    checker = get_syntax_checker()
    
    # Valid Python
    valid_code = """
def hello(name):
    return f"Hello, {name}!"

print(hello("World"))
"""
    result = checker.check(valid_code, "python")
    print(f"✓ Valid Python: {result.is_valid}")
    
    # Invalid Python
    invalid_code = """
def broken(
    return "missing param"
"""
    result = checker.check(invalid_code, "python")
    print(f"✓ Invalid Python detected: {not result.is_valid}")
    if result.error_message:
        print(f"  Error: {result.error_message}")


async def main():
    """Run all tests."""
    print("=" * 50)
    print("CONTENT GENERATION PIPELINE TESTS")
    print("=" * 50)
    
    try:
        # # Basic tests (no API)
        # await test_syntax_checker()
        
        # # Diagram tests
        # await test_diagram_generation()
        
        # # LLM-based tests (require API)
        # await test_content_planner()
        # await test_lab_generation()
        
        # Image generation test
        # await test_image_generation()
        
        # Full pipeline
        # await test_full_pipeline()
        
        # Optional: Full pipeline with images (takes longer)
        await test_full_pipeline_with_images()
        
        print("\n" + "=" * 50)
        print("ALL TESTS COMPLETED ✓")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

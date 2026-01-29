"""
Quick test to verify content generation fixes.
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


async def test_all_fixes():
    """Test all fixes: paths, diagrams, empty lists."""
    print("=" * 60)
    print("TESTING CONTENT GENERATION FIXES")
    print("=" * 60)
    
    config = PipelineConfig(
        output_dir="./test_output",
        generate_images=True,
        generate_diagrams=True,
        num_pages=3  # Short test
    )
    
    pipeline = get_content_pipeline(config)
    
    print("\n[1/3] Generating content...")
    result = await pipeline.generate_theory(
        topic="Introduction to Hash Tables",
        output_type="markdown"
    )
    
    if not result.success:
        print(f"✗ Generation failed: {result.error}")
        return
    
    print(f"✓ Content generated: {result.output_path}")
    
    # Read generated markdown to check fixes
    print("\n[2/3] Checking fixes...")
    with open(result.output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check 1: Image paths should use forward slashes and simple format
    issues = []
    if '\\images\\' in content or '\\diagrams\\' in content:
        issues.append("✗ Backslashes found in paths (should be forward slashes)")
    else:
        print("✓ Path format: Using forward slashes")
    
    # Check 2: Should have image/diagram links, not just mermaid code blocks
    image_links = content.count('](images/')
    diagram_links = content.count('](diagrams/')
    mermaid_blocks = content.count('```mermaid')
    
    print(f"  - Image links: {image_links}")
    print(f"  - Diagram links: {diagram_links}")
    print(f"  - Mermaid code blocks: {mermaid_blocks}")
    
    if diagram_links > 0:
        print("✓ Diagrams: Rendered as images (not code blocks)")
    elif mermaid_blocks > 0:
        issues.append("✗ Diagrams still as mermaid code (should be image links)")
    
    # Check 3: Look for empty lists
    import re
    empty_list_pattern = r'-\s*\n-'  # Pattern for empty bullet points
    if re.search(empty_list_pattern, content):
        issues.append("✗ Empty list items found")
    else:
        print("✓ Lists: No empty items detected")
    
    print("\n[3/3] Summary:")
    if issues:
        print("\n⚠ Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✓ All fixes working correctly!")
    
    print(f"\nGenerated files:")
    print(f"  - Markdown: {result.output_path}")
    print(f"  - Assets: {len(result.assets)} files")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all_fixes())

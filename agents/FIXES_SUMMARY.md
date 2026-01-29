# Content Generation Fixes - Summary

## Issues Fixed

### 1. Image & Diagram Path Format
**Problem:** Paths using backslashes and absolute paths
**Fix:** Simplified to `images/file.png` and `diagrams/file.png` with forward slashes

```python
def _make_relative_path(self, absolute_path: str) -> str:
    abs_path = Path(absolute_path)
    parent_name = abs_path.parent.name
    filename = abs_path.name
    return f"{parent_name}/{filename}"  # Simple format
```

### 2. Diagrams Not Rendering as Images
**Problem:** Mermaid code blocks appearing in markdown instead of diagram images
**Fix:** Check if diagram was rendered and use image link instead

```python
elif element_type == 'diagram':
    diagram = content.diagrams[idx]
    if image_paths and diagram.id in image_paths:
        # Use rendered diagram image
        diagram_path = self._make_relative_path(image_paths[diagram.id])
        lines.append(f"![{caption}]({diagram_path})")
    else:
        # Fallback to mermaid code
        lines.append("```mermaid")
```

### 3. Duplicate Mermaid Type Declarations
**Problem:** AI generating `flowchart TD` when code already has `graph TD`, causing parse errors
**Fix:** 
- Updated prompt to not include type declarations
- Enhanced `_fix_code()` to detect and remove duplicates

```python
# In theory_writer.py prompt
NOTE: For mermaid diagrams:
- DO NOT include type declarations (flowchart TD, sequenceDiagram, etc.)
- Only include the diagram content/nodes
```

### 4. Empty List Items
**Problem:** Lists with empty `<item>` tags rendering as blank bullets
**Fix:** Filter out empty items and update prompt

```python
items = [item.strip() for item in lst['items'] if item and item.strip()]
if items:  # Only render if non-empty
    for i, item in enumerate(items):
        lines.append(f"- {item}")
```

Prompt update:
```
6. IMPORTANT: All lists MUST have at least 3-5 items with actual content
7. NEVER create empty list items - each <item> must have meaningful text
8. For "Key Takeaways" sections, provide concrete, actionable insights
```

### 5. Mermaid Validation with Gemini
**Problem:** No automatic correction for invalid mermaid syntax
**Fix:** Retry with Gemini-powered correction

```python
async def render(self, diagram: ParsedMermaid):
    max_retries = 2
    for attempt in range(max_retries):
        success, result, error = await self._try_render(code, diagram.id)
        if success:
            return result
        # Fix with Gemini
        if attempt < max_retries - 1:
            fixed_code = await self._fix_mermaid_with_gemini(code, type, error)
```

## Files Modified

1. `content_gen_engine/generators/markdown_generator.py`
   - Simplified `_make_relative_path()`
   - Updated diagram rendering to use images
   - Added empty list filtering

2. `content_gen_engine/generators/diagram_generator.py`
   - Enhanced `_fix_code()` for duplicate declarations
   - Added `_fix_mermaid_with_gemini()` for auto-correction
   - Added retry logic in `render()`

3. `content_gen_engine/agents/theory_writer.py`
   - Updated prompt with explicit mermaid instructions
   - Added list population rules

4. `services/gemini_service.py`
   - Added `generate_structured()` method for schema-based output

## Testing

Run the test:
```bash
cd agents
python test_fixes.py
```

Expected output:
- ✓ Path format: Forward slashes
- ✓ Diagrams: Rendered as images
- ✓ Lists: No empty items
- ✓ All fixes working correctly

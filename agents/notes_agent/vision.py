"""
Gemini Vision integration for extracting text from handwritten note images.
"""

import base64
import json
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from config.settings import settings
from utils.logger import logger


class VisionProcessor:
    """
    Processes handwritten note images using Gemini Vision API.
    Extracts text and structure from images.
    """
    
    EXTRACTION_PROMPT = """You are an expert at reading and digitizing handwritten notes into beautifully structured, colorful, and professionally styled content.

Analyze this handwritten note image and extract ALL content with rich semantic structure.

Return a JSON object with this exact format:
{
    "title": "Topic title from the notes",
    "blocks": [
        {
            "type": "section|subsection|paragraph|equation|list|numbered_list|definition|theorem|example|note|warning|proof|code|diagram|table",
            "content": "The content (see format guidelines below)",
            "confidence": 0.95,
            "metadata": {}
        }
    ],
    "full_text": "Complete plain text extraction"
}

## Block Type Guidelines:

### Structure Types:
- **section**: Main headings - just the heading text
- **subsection**: Subheadings - just the subheading text
- **paragraph**: Regular text content

### Math Types:
- **equation**: Mathematical formulas in LaTeX format
  - Use $...$ for inline math
  - Use $$...$$ for display math (important equations)
  - Support align, matrix, cases environments

### List Types:
- **list**: Bullet point items (separate items with newlines)
- **numbered_list**: Numbered items (separate items with newlines)

### Highlighted Content Boxes (identify from context, emphasis, or boxing):
- **definition**: Formal definitions, marked terms, or "Definition:" labels
  Format: "Term: Description" or just the definition text
  metadata: {"term": "Term Name"} if applicable

- **theorem**: Theorems, laws, formulas, or key principles
  Format: The theorem statement
  metadata: {"name": "Theorem Name"} if applicable

- **example**: Worked examples, sample problems, solutions
  Format: The example content
  metadata: {"title": "Example Title"} if applicable

- **note**: Important remarks, tips, observations, "Note:" or "NB:" labels
  Format: The note content

- **warning**: Warnings, common mistakes, cautions, "Warning:" or "⚠" labels
  Format: The warning content

- **proof**: Mathematical proofs, derivations
  Format: The proof steps

### Special Content:
- **code**: Programming code snippets
  Format: The code text
  metadata: {"language": "python|javascript|c|cpp|java|etc"}

- **diagram**: Flowcharts, trees, graphs, mind maps
  Convert the visual diagram to Mermaid.js syntax:
  - Flowcharts: "graph TD\\n  A[Start] --> B[Process] --> C{Decision}\\n  C -->|Yes| D[Result]\\n  C -->|No| E[Alternative]"
  - Trees: "graph TD\\n  Root --> Child1\\n  Root --> Child2\\n  Child1 --> Leaf1"
  - Sequence: "sequenceDiagram\\n  A->>B: Message\\n  B-->>A: Reply"
  metadata: {"type": "flowchart|tree|sequence|mindmap"}

- **table**: Tables with data
  Format as JSON string: {"headers": ["Col1", "Col2"], "rows": [["a", "b"], ["c", "d"]], "caption": "Optional caption"}
  metadata: {"caption": "Table caption"} if applicable

## Guidelines:
1. **Preserve hierarchy**: Detect headings vs body content
2. **Semantic labeling**: If content looks like a definition, theorem, or example, label it appropriately even if not explicitly marked
3. **LaTeX for all math**: Use proper LaTeX notation for all mathematical expressions
4. **Diagram conversion**: Interpret hand-drawn diagrams and convert to Mermaid.js format
5. **Complete extraction**: Include ALL readable text, even if partially visible
6. **Logical ordering**: Maintain the original reading order
7. **Rich structure**: Prefer specific block types over generic "paragraph" when applicable

IMPORTANT: Return ONLY valid JSON, no markdown code blocks or formatting."""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
    
    async def extract_from_image(
        self, 
        image_base64: str,
        mime_type: str = "image/png"
    ) -> Dict[str, Any]:
        """
        Extract text and structure from a handwritten note image.
        
        Args:
            image_base64: Base64 encoded image data
            mime_type: Image MIME type (image/png, image/jpeg, etc.)
            
        Returns:
            Dictionary with extracted blocks, title, and full text
        """
        try:
            # Decode base64 to bytes
            image_data = base64.b64decode(image_base64)
            
            # Create image part for Gemini
            image_part = {
                "mime_type": mime_type,
                "data": image_data
            }
            
            # Send to Gemini Vision
            logger.info("Sending image to Gemini Vision for extraction...")
            response = self.model.generate_content(
                [self.EXTRACTION_PROMPT, image_part],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 4096,
                }
            )
            
            # Debug: Print raw response
            print(f"\n{'='*50}")
            print("GEMINI VISION RAW RESPONSE:")
            print(f"{'='*50}")
            print(response.text[:2000] if response.text else "No response")
            print(f"{'='*50}\n")
            
            # Parse JSON response
            result = self._parse_response(response.text)
            logger.info(f"Extracted {len(result.get('blocks', []))} content blocks")
            
            return result
            
        except Exception as e:
            logger.error(f"Vision extraction error: {type(e).__name__}: {e}")
            return {
                "title": "Untitled Note",
                "blocks": [],
                "full_text": "",
                "error": str(e)
            }
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the JSON response from Gemini."""
        try:
            # Clean up response - remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Return raw text as a single block
            return {
                "title": "Extracted Notes",
                "blocks": [
                    {
                        "type": "paragraph",
                        "content": response_text,
                        "confidence": 0.5
                    }
                ],
                "full_text": response_text
            }


# Singleton instance
_vision_processor: Optional[VisionProcessor] = None


def get_vision_processor() -> VisionProcessor:
    """Get or create the vision processor instance."""
    global _vision_processor
    if _vision_processor is None:
        _vision_processor = VisionProcessor()
    return _vision_processor

"""
Gemini Vision integration for extracting text from handwritten note images.
"""

import base64
import json
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types
from config.settings import settings
from utils.logger import logger


class VisionProcessor:
    """
    Processes handwritten note images using Gemini Vision API.
    Extracts text and structure from images.
    """

    EXTRACTION_PROMPT = """You are an expert at reading handwritten notes and converting them to perfectly formatted LaTeX.

Analyze this handwritten note image and extract ALL content with proper LaTeX formatting.

Return a JSON object with this exact format:
{
    "title": "Topic title from the notes",
    "blocks": [
        {
            "type": "section|subsection|paragraph|equation|list|numbered_list|definition|theorem|example|note|warning|proof|code|diagram|table",
            "content": "The content with CORRECT LaTeX",
            "confidence": 0.95,
            "metadata": {}
        }
    ],
    "full_text": "Complete plain text extraction"
}

## LaTeX Math Formatting Rules (CRITICAL - FOLLOW EXACTLY):

### Inline Math (use $...$):
- Variables: $x$, $y$, $z$
- Simple expressions: $x + y = z$
- Greek letters: $\\alpha$, $\\beta$, $\\gamma$, $\\theta$, $\\pi$, $\\lambda$, $\\sigma$, $\\omega$
- Subscripts: $x_1$, $x_n$, $a_{i,j}$
- Superscripts: $x^2$, $e^{-x}$, $a^{n+1}$
- Fractions (inline): $\\frac{a}{b}$, $\\frac{dy}{dx}$

### Display Math (use $$...$$):
- Important equations: $$E = mc^2$$
- Fractions: $$\\frac{a + b}{c - d}$$
- Square roots: $$\\sqrt{x^2 + y^2}$$
- Sums: $$\\sum_{i=1}^{n} x_i$$
- Integrals: $$\\int_0^\\infty e^{-x} dx$$
- Products: $$\\prod_{i=1}^{n} a_i$$
- Limits: $$\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$$

### Common Patterns:
- Derivatives: $\\frac{d}{dx}$, $\\frac{\\partial f}{\\partial x}$
- Matrices: $$\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$$
- Cases: $$f(x) = \\begin{cases} 1 & \\text{if } x > 0 \\\\ 0 & \\text{otherwise} \\end{cases}$$
- Aligned equations: $$\\begin{align} a &= b + c \\\\ &= d + e \\end{align}$$

### COMMON MISTAKES TO AVOID:
- DON'T write \\frac12, write \\frac{1}{2}
- DON'T forget braces: write x_{ij} not x_ij for multi-char subscripts
- DON'T mix $ with $$: choose one style per expression
- DON'T escape inside math: \\alpha not \\\\alpha
- DON'T forget \\text{} for words in math: $x = 5 \\text{ where } x > 0$

## Block Type Guidelines:

### Structure Types:
- **section**: Main headings - just the heading text
- **subsection**: Subheadings - just the subheading text
- **paragraph**: Regular text content (may contain inline math)

### Math Types:
- **equation**: Display math equations (use $$...$$ notation)

### List Types:
- **list**: Bullet point items (separate items with newlines)
- **numbered_list**: Numbered items (separate items with newlines)

### Highlighted Content Boxes:
- **definition**: Formal definitions, terms with "Definition:" label
  metadata: {"term": "Term Name"} if applicable
- **theorem**: Theorems, laws, formulas, key principles
  metadata: {"name": "Theorem Name"} if applicable
- **example**: Worked examples, sample problems, solutions
  metadata: {"title": "Example Title"} if applicable
- **note**: Important remarks, tips, observations
- **warning**: Cautions, common mistakes
- **proof**: Mathematical proofs, derivations

### Special Content:
- **code**: Programming code (metadata: {"language": "python|javascript|etc"})
- **diagram**: Convert to Mermaid.js syntax (metadata: {"type": "flowchart|tree|sequence"})
- **table**: JSON format: {"headers": [...], "rows": [[...], ...]}

## Guidelines:
1. **Verify LaTeX syntax**: Every equation must be syntactically correct
2. **Use proper braces**: Always use {} for multi-character subscripts/superscripts
3. **Greek letters**: Use proper LaTeX commands (\\alpha, \\beta, etc.)
4. **Preserve hierarchy**: Detect headings vs body content
5. **Complete extraction**: Include ALL readable text
6. **Logical ordering**: Maintain the original reading order

IMPORTANT: Return ONLY valid JSON, no markdown code blocks or formatting."""

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.0-flash"

    async def extract_from_image(
        self, image_base64: str, mime_type: str = "image/png"
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
            image_part = types.Part.from_bytes(data=image_data, mime_type=mime_type)

            # Send to Gemini Vision
            logger.info("Sending image to Gemini Vision for extraction...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[self.EXTRACTION_PROMPT, image_part],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                ),
            )

            # Debug: Print raw response
            print(f"\n{'=' * 50}")
            print("GEMINI VISION RAW RESPONSE:")
            print(f"{'=' * 50}")
            print(response.text[:2000] if response.text else "No response")
            print(f"{'=' * 50}\n")

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
                "error": str(e),
            }

    async def extract_from_multiple_images(
        self, images: list, mime_types: list = None, merge_related: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from multiple images and intelligently merge related content.

        Args:
            images: List of base64 encoded images
            mime_types: List of MIME types for each image
            merge_related: Whether to merge related content

        Returns:
            Dictionary with merged blocks, title, and full text
        """
        if not images:
            return {
                "title": "Empty",
                "blocks": [],
                "full_text": "",
                "error": "No images provided",
            }

        if len(images) == 1:
            mime_type = mime_types[0] if mime_types else "image/png"
            return await self.extract_from_image(images[0], mime_type)

        try:
            # Prepare all images for Gemini
            image_parts = []
            for i, img_base64 in enumerate(images):
                image_data = base64.b64decode(img_base64)
                mime_type = (
                    mime_types[i] if mime_types and i < len(mime_types) else "image/png"
                )
                image_parts.append(
                    types.Part.from_bytes(data=image_data, mime_type=mime_type)
                )

            # Create multi-image prompt
            multi_prompt = f"""You are analyzing {len(images)} images of handwritten notes.

{self.EXTRACTION_PROMPT}

ADDITIONAL INSTRUCTIONS FOR MULTIPLE IMAGES:
1. Analyze all {len(images)} images together
2. Determine if they are RELATED (same topic/lecture) or UNRELATED
3. If RELATED: Merge content into a single coherent document, maintaining logical flow
4. If UNRELATED: Keep content separate with clear section breaks between different topics
5. Mark each block with the source image index (1-indexed) in the response

For each block, add "source_image": <image_number> (1 to {len(images)})

Return a single JSON object with merged/organized content:
{{
    "title": "Document title",
    "is_related": true/false,
    "blocks": [...],
    "full_text": "Complete merged text"
}}"""

            logger.info(f"Processing {len(images)} images together...")

            # Send all images with the prompt
            contents = [multi_prompt] + image_parts
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=8192,  # More tokens for multiple images
                ),
            )

            result = self._parse_response(response.text)
            result["image_count"] = len(images)
            result["merged"] = result.get("is_related", True)

            logger.info(
                f"Extracted {len(result.get('blocks', []))} blocks from {len(images)} images"
            )
            return result

        except Exception as e:
            logger.error(f"Multi-image extraction error: {type(e).__name__}: {e}")
            return {
                "title": "Extraction Failed",
                "blocks": [],
                "full_text": "",
                "error": str(e),
                "image_count": len(images),
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
                    {"type": "paragraph", "content": response_text, "confidence": 0.5}
                ],
                "full_text": response_text,
            }


# Singleton instance
_vision_processor: Optional[VisionProcessor] = None


def get_vision_processor() -> VisionProcessor:
    """Get or create the vision processor instance."""
    global _vision_processor
    if _vision_processor is None:
        _vision_processor = VisionProcessor()
    return _vision_processor

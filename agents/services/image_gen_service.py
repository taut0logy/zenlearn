"""
Image Generation Service - Gemini Imagen.

Uses Gemini's native image generation capabilities.
"""

from google import genai
from google.genai import types
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path
import base64
import os

from config.settings import settings
from utils.logger import logger


@dataclass
class ImageConfig:
    """Configuration for image generation."""
    aspect_ratio: str = "16:9"  # 1:1, 4:3, 16:9, 9:16
    resolution: str = "1K"  # 1K, 2K
    output_format: str = "png"
    style_preset: Optional[str] = None


class ImageGenService:
    """
    Image generation using Gemini Imagen.
    
    Provides 500 free images/day with Gemini API.
    """
    
    MODEL = "imagen-4.0-generate-001"
    
    def __init__(self, output_dir: str = "./assets/images"):
        """Initialize image generation service."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.default_config = ImageConfig()
    
    async def generate(
        self,
        prompt: str,
        filename: Optional[str] = None,
        config: Optional[ImageConfig] = None
    ) -> str:
        """
        Generate image from prompt.
        
        Args:
            prompt: Image description
            filename: Output filename (without extension)
            config: Image configuration
            
        Returns:
            Path to generated image
        """
        cfg = config or self.default_config
        
        # Enhance prompt for educational content
        enhanced_prompt = self._enhance_prompt(prompt, cfg.style_preset)
        
        try:
            response = self.client.models.generate_images(
                model=self.MODEL,
                prompt=enhanced_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=cfg.aspect_ratio,
                    output_mime_type=f"image/{cfg.output_format}",
                    include_rai_reason=True
                )
            )
            
            if not response.generated_images:
                raise ValueError("No images generated")
            
            # Save image
            image = response.generated_images[0].image
            
            if not filename:
                import uuid
                filename = f"img_{uuid.uuid4().hex[:8]}"
            
            output_path = self.output_dir / f"{filename}.{cfg.output_format}"
            image.save(str(output_path))
            
            logger.info(f"Generated image: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    async def generate_batch(
        self,
        prompts: List[dict],
        config: Optional[ImageConfig] = None
    ) -> dict:
        """
        Generate multiple images.
        
        Args:
            prompts: List of {"id": str, "prompt": str}
            config: Image configuration
            
        Returns:
            Dict mapping IDs to file paths
        """
        results = {}
        
        for item in prompts:
            try:
                path = await self.generate(
                    prompt=item["prompt"],
                    filename=item.get("id"),
                    config=config
                )
                results[item["id"]] = path
            except Exception as e:
                logger.warning(f"Failed to generate {item['id']}: {e}")
                results[item["id"]] = None
        
        return results
    
    def _enhance_prompt(self, prompt: str, style: Optional[str] = None) -> str:
        """Enhance prompt for educational illustrations."""
        
        base_modifiers = [
            "clean educational illustration",
            "professional diagram style",
            "clear and easy to understand",
            "high contrast for readability",
            "white or light background"
        ]
        
        if style:
            base_modifiers.append(style)
        
        return f"{prompt}, {', '.join(base_modifiers)}"


# Factory
def get_image_gen_service(output_dir: str = "./assets/images") -> ImageGenService:
    """Get image generation service instance."""
    return ImageGenService(output_dir=output_dir)

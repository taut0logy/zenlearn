"""
Gemini LLM Service - Updated for Gemini 3 Pro.

Uses google-genai SDK directly for better control.
"""

from google import genai
from google.genai import types
from typing import Optional, Dict, Any, List, AsyncIterator
from dataclasses import dataclass
import json
import asyncio

from config.settings import settings
from utils.logger import logger


@dataclass
class GenerationConfig:
    """Configuration for content generation."""
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192
    system_instruction: Optional[str] = None
    response_mime_type: Optional[str] = None  # "application/json" for JSON mode


class GeminiService:
    """
    Gemini LLM service using google-genai SDK.
    
    Supports:
    - Text generation
    - JSON mode
    - Streaming
    - System instructions
    """
    
    # Available models
    MODELS = {
        "pro": "gemini-3-pro-preview",
        "flash": "gemini-3-flash-preview",
        "pro_image": "imagen-4.0-fast-generate-001",
    }
    
    def __init__(self, model: str = "pro"):
        """Initialize Gemini client."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = self.MODELS.get(model, model)
        self.default_config = GenerationConfig()
    
    async def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate text content.
        
        Args:
            prompt: User prompt
            config: Generation configuration
            context: Optional context to include
            
        Returns:
            Generated text
        """
        cfg = config or self.default_config
        
        # Build contents
        contents = prompt
        if context:
            contents = f"Context:\n{context}\n\nRequest:\n{prompt}"
        
        try:
            # Build config
            gen_config = types.GenerateContentConfig(
                temperature=cfg.temperature,
                top_p=cfg.top_p,
                top_k=cfg.top_k,
                max_output_tokens=cfg.max_output_tokens,
            )
            
            if cfg.system_instruction:
                gen_config.system_instruction = cfg.system_instruction
            
            if cfg.response_mime_type:
                gen_config.response_mime_type = cfg.response_mime_type
            
            # Generate
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=gen_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        schema_hint: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON output.
        
        Args:
            prompt: Prompt requesting JSON output
            schema_hint: Optional JSON schema description
            config: Generation config
            
        Returns:
            Parsed JSON dict
        """
        cfg = config or GenerationConfig(
            temperature=0.3,  # Lower for structured output
            response_mime_type="application/json"
        )
        
        enhanced_prompt = prompt
        if schema_hint:
            enhanced_prompt = f"{prompt}\n\nExpected JSON format:\n{schema_hint}"
        
        result = await self.generate(enhanced_prompt, cfg)
        
        # Parse JSON
        try:
            # Handle markdown code blocks
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            return json.loads(result.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed, returning raw: {e}")
            return {"raw_response": result}
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        config: Optional[GenerationConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate structured output with strict schema adherence.
        
        Uses response_json_schema for guaranteed schema compliance.
        
        Args:
            prompt: User prompt
            response_schema: JSON schema dict
            config: Generation configuration
            
        Returns:
            Parsed JSON dict matching schema
        """
        cfg = config or GenerationConfig(
            temperature=0.3,  # Lower for structured output
        )
        
        try:
            # Build config with schema
            gen_config = types.GenerateContentConfig(
                temperature=cfg.temperature,
                top_p=cfg.top_p,
                top_k=cfg.top_k,
                max_output_tokens=cfg.max_output_tokens,
                response_mime_type="application/json",
                response_schema=response_schema
            )
            
            if cfg.system_instruction:
                gen_config.system_instruction = cfg.system_instruction
            
            # Generate
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=gen_config
            )
            
            # Parse JSON
            result = response.text.strip()
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncIterator[str]:
        """
        Stream generated content.
        
        Yields chunks of text as they're generated.
        """
        cfg = config or self.default_config
        
        try:
            gen_config = types.GenerateContentConfig(
                temperature=cfg.temperature,
                top_p=cfg.top_p,
                max_output_tokens=cfg.max_output_tokens,
            )
            
            if cfg.system_instruction:
                gen_config.system_instruction = cfg.system_instruction
            
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=gen_config
            ):
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        config: Optional[GenerationConfig] = None
    ) -> str:
        """
        Multi-turn chat.
        
        Args:
            messages: List of {"role": "user"|"model", "content": "..."}
            config: Generation config
            
        Returns:
            Model response
        """
        cfg = config or self.default_config
        
        try:
            chat = self.client.chats.create(model=self.model)
            
            # Replay conversation
            for msg in messages[:-1]:
                if msg["role"] == "user":
                    chat.send_message(msg["content"])
            
            # Get response for last message
            response = chat.send_message(messages[-1]["content"])
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini chat failed: {e}")
            raise


# Factory functions
def get_gemini_service(model: str = "pro") -> GeminiService:
    """Get Gemini service instance."""
    return GeminiService(model=model)


# Singleton for convenience
gemini_service = GeminiService()

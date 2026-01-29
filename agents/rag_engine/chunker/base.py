"""
Base classes and data models for chunking.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import hashlib

# Try to import tiktoken for token counting
try:
    import tiktoken
    _encoder = tiktoken.get_encoding("cl100k_base")
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


@dataclass
class Chunk:
    """A single chunk of content."""
    content: str
    metadata: Dict[str, Any]
    token_count: int
    chunk_id: Optional[str] = None
    
    def __post_init__(self):
        if self.chunk_id is None:
            self.chunk_id = generate_chunk_id(self.content)


@dataclass
class ChunkingConfig:
    """Configuration for chunking."""
    min_tokens: int = 100
    max_tokens: int = 800
    target_tokens: int = 400
    overlap_tokens: int = 50


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken or fallback."""
    if HAS_TIKTOKEN:
        return len(_encoder.encode(text))
    # Fallback: approximate 4 chars per token
    return len(text) // 4


def generate_chunk_id(content: str) -> str:
    """Generate unique ID for chunk content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


class BaseChunker(ABC):
    """Abstract base class for all chunkers."""
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
    
    @abstractmethod
    def chunk(self, content: Any, metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Chunk content into smaller pieces.
        
        Args:
            content: Content to chunk (format depends on chunker type)
            metadata: Base metadata to attach to all chunks
            
        Returns:
            List of Chunk objects
        """
        pass
    
    def _merge_metadata(
        self, 
        base: Dict[str, Any], 
        chunk_specific: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge base metadata with chunk-specific metadata."""
        return {**base, **chunk_specific}

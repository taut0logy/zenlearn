"""
Chunker Module - Content-aware chunking for RAG.

Public API:
    - ChunkingService: Unified chunking interface
    - get_chunking_service(): Factory function
    - Chunk: Chunk data model
    - Individual chunkers for specific use cases
"""

from .base import (
    Chunk,
    ChunkingConfig,
    BaseChunker,
    count_tokens,
    generate_chunk_id,
)
from .chunking_service import (
    ChunkingService,
    get_chunking_service,
    chunking_service,
)
from .slide_chunker import (
    SlideChunker,
    SlideContent,
    get_slide_chunker,
)
from .pdf_chunker import (
    PDFChunker,
    PDFPage,
    get_pdf_chunker,
)
from .code_chunker import (
    CodeChunker,
    get_code_chunker,
)

__all__ = [
    # Main API
    'ChunkingService',
    'get_chunking_service',
    'chunking_service',
    
    # Data models
    'Chunk',
    'ChunkingConfig',
    'SlideContent',
    'PDFPage',
    
    # Base
    'BaseChunker',
    'count_tokens',
    'generate_chunk_id',
    
    # Individual chunkers
    'SlideChunker',
    'get_slide_chunker',
    'PDFChunker',
    'get_pdf_chunker',
    'CodeChunker',
    'get_code_chunker',
]

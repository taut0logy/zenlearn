# Re-export from base for backward compatibility
from .base import Chunk, ChunkingConfig, count_tokens, generate_chunk_id

__all__ = ['Chunk', 'ChunkingConfig', 'count_tokens', 'generate_chunk_id']

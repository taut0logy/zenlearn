"""
Unified Chunking Service.

Provides a single interface for chunking any supported file type.
"""

import os
from typing import List, Dict, Any, Optional, Union

from .base import Chunk, ChunkingConfig
from .slide_chunker import SlideChunker, get_slide_chunker
from .pdf_chunker import PDFChunker, get_pdf_chunker
from .code_chunker import CodeChunker, get_code_chunker
from rag_engine.code_processor import CodePreprocessor, CodeAnalysisResult
from utils.logger import logger


class ChunkingService:
    """
    Unified service for chunking different file types.
    
    Usage:
        service = ChunkingService()
        chunks = service.chunk_file("path/to/file.pptx", {"course_id": "123"})
        chunks = await service.chunk_file_with_llm("path/to/code.py", metadata)
    """
    
    # Supported file extensions
    SLIDE_EXTENSIONS = {'.pptx', '.ppt'}
    PDF_EXTENSIONS = {'.pdf'}
    CODE_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb'}
    
    def __init__(
        self,
        slide_config: Optional[ChunkingConfig] = None,
        pdf_config: Optional[ChunkingConfig] = None,
        code_config: Optional[ChunkingConfig] = None
    ):
        self.slide_chunker = get_slide_chunker(slide_config)
        self.pdf_chunker = get_pdf_chunker(pdf_config)
        self.code_chunker = get_code_chunker(code_config)
        self.code_preprocessor = CodePreprocessor()
    
    def chunk_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Chunk a file based on its type.
        
        Args:
            file_path: Path to the file
            metadata: Optional base metadata
            
        Returns:
            List of Chunk objects
        """
        metadata = metadata or {}
        metadata['source_file'] = file_path
        metadata['filename'] = os.path.basename(file_path)
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in self.SLIDE_EXTENSIONS:
            return self.slide_chunker.chunk(file_path, metadata)
        elif ext in self.PDF_EXTENSIONS:
            return self.pdf_chunker.chunk(file_path, metadata)
        elif ext in self.CODE_EXTENSIONS:
            return self.code_chunker.chunk(file_path, metadata)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    async def chunk_file_with_llm(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Chunk a code file with LLM-enriched metadata.
        
        Only applies to code files - other types are chunked normally.
        
        Args:
            file_path: Path to the file
            metadata: Optional base metadata
            
        Returns:
            List of enriched Chunk objects
        """
        metadata = metadata or {}
        metadata['source_file'] = file_path
        metadata['filename'] = os.path.basename(file_path)
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in self.CODE_EXTENSIONS:
            # Read code
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Run LLM analysis
            logger.info(f"Running LLM analysis on {file_path}")
            analysis = await self.code_preprocessor.process(code, metadata['filename'])
            
            # Chunk with enriched metadata
            return self.code_chunker.chunk_with_llm_metadata(code, metadata, analysis)
        else:
            # For non-code files, use normal chunking
            return self.chunk_file(file_path, metadata)
    
    def chunk_content(
        self,
        content: str,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Chunk raw content by specifying type.
        
        Args:
            content: Raw content string
            content_type: One of 'code', 'pdf', 'text'
            metadata: Optional base metadata
            
        Returns:
            List of Chunk objects
        """
        metadata = metadata or {}
        
        if content_type == 'code':
            return self.code_chunker.chunk(content, metadata)
        elif content_type == 'pdf' or content_type == 'text':
            return self.pdf_chunker.chunk_from_text(content, metadata)
        else:
            raise ValueError(f"Unknown content type: {content_type}")
    
    async def chunk_code_with_llm(
        self,
        code: str,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Chunk], CodeAnalysisResult]:
        """
        Chunk code content with LLM analysis.
        
        Args:
            code: Source code string
            filename: Filename for language detection
            metadata: Optional base metadata
            
        Returns:
            Tuple of (chunks, analysis_result)
        """
        metadata = metadata or {}
        metadata['filename'] = filename
        
        # Run LLM analysis
        analysis = await self.code_preprocessor.process(code, filename)
        
        # Chunk with enriched metadata
        chunks = self.code_chunker.chunk_with_llm_metadata(code, metadata, analysis)
        
        return chunks, analysis
    
    def get_supported_extensions(self) -> Dict[str, List[str]]:
        """Get dict of supported extensions by type."""
        return {
            'slides': list(self.SLIDE_EXTENSIONS),
            'pdf': list(self.PDF_EXTENSIONS),
            'code': list(self.CODE_EXTENSIONS),
        }


# Factory function
def get_chunking_service(
    slide_config: Optional[ChunkingConfig] = None,
    pdf_config: Optional[ChunkingConfig] = None,
    code_config: Optional[ChunkingConfig] = None
) -> ChunkingService:
    """Create a chunking service instance."""
    return ChunkingService(slide_config, pdf_config, code_config)


# Singleton for convenience
chunking_service = ChunkingService()

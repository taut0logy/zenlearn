"""
PDF Chunker - Section-aware chunking for PDF documents.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from .base import BaseChunker, Chunk, ChunkingConfig, count_tokens

# Try to import pymupdf
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


@dataclass
class PDFPage:
    """Extracted content from a PDF page."""
    page_number: int
    text: str
    headers: List[Tuple[int, str]]  # (level, text)


class PDFChunker(BaseChunker):
    """
    Chunker for PDF documents.
    
    Strategy:
    - Detect section boundaries via headers
    - Chunk within sections using size limits
    - Track page numbers for citation
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        default_config = ChunkingConfig(
            min_tokens=150,
            max_tokens=1000,
            target_tokens=500,
            overlap_tokens=75
        )
        super().__init__(config or default_config)
    
    def chunk(
        self,
        content: Any,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """
        Chunk a PDF file.
        
        Args:
            content: Path to PDF file
            metadata: Base metadata
            
        Returns:
            List of chunks
        """
        if not HAS_PYMUPDF:
            raise ImportError("pymupdf required: pip install pymupdf")
        
        file_path = content
        pages = self._extract_pages(file_path)
        
        return self._chunk_pages(pages, metadata)
    
    def chunk_from_text(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Chunk from raw text (fallback when PDF extraction already done)."""
        return self._chunk_text(text, metadata)
    
    def _extract_pages(self, file_path: str) -> List[PDFPage]:
        """Extract pages from PDF."""
        doc = fitz.open(file_path)
        pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            
            text_parts = []
            headers = []
            
            for block in blocks:
                if block["type"] == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text:
                                font_size = span.get("size", 12)
                                
                                # Detect headers by font size
                                if font_size > 14:
                                    level = 1 if font_size > 18 else 2
                                    headers.append((level, text))
                                
                                text_parts.append(text)
            
            pages.append(PDFPage(
                page_number=page_num + 1,
                text="\n".join(text_parts),
                headers=headers
            ))
        
        doc.close()
        return pages
    
    def _chunk_pages(
        self,
        pages: List[PDFPage],
        base_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Chunk pages with section awareness."""
        chunks = []
        current_section = None
        buffer_text = []
        buffer_pages = []
        buffer_tokens = 0
        
        for page in pages:
            # Check for section headers
            for level, header in page.headers:
                if level == 1:
                    # Flush buffer on major section
                    if buffer_text:
                        chunks.append(self._create_chunk(
                            "\n".join(buffer_text),
                            buffer_pages,
                            current_section,
                            base_metadata
                        ))
                        buffer_text = []
                        buffer_pages = []
                        buffer_tokens = 0
                    current_section = header
            
            page_tokens = count_tokens(page.text)
            
            # Check if adding page exceeds max
            if buffer_tokens + page_tokens > self.config.max_tokens:
                if buffer_text:
                    chunks.append(self._create_chunk(
                        "\n".join(buffer_text),
                        buffer_pages,
                        current_section,
                        base_metadata
                    ))
                
                # If single page too large, split it
                if page_tokens > self.config.max_tokens:
                    page_chunks = self._split_large_text(
                        page.text,
                        [page.page_number],
                        current_section,
                        base_metadata
                    )
                    chunks.extend(page_chunks)
                    buffer_text = []
                    buffer_pages = []
                    buffer_tokens = 0
                else:
                    buffer_text = [page.text]
                    buffer_pages = [page.page_number]
                    buffer_tokens = page_tokens
            else:
                buffer_text.append(page.text)
                buffer_pages.append(page.page_number)
                buffer_tokens += page_tokens
        
        # Flush remaining
        if buffer_text:
            chunks.append(self._create_chunk(
                "\n".join(buffer_text),
                buffer_pages,
                current_section,
                base_metadata
            ))
        
        return chunks
    
    def _chunk_text(
        self,
        text: str,
        base_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Chunk raw text by sentences."""
        sentences = self._split_sentences(text)
        chunks = []
        buffer = []
        buffer_tokens = 0
        
        for sentence in sentences:
            sent_tokens = count_tokens(sentence)
            
            if buffer_tokens + sent_tokens > self.config.max_tokens:
                if buffer:
                    chunks.append(self._create_chunk(
                        " ".join(buffer),
                        [],
                        None,
                        base_metadata
                    ))
                buffer = [sentence]
                buffer_tokens = sent_tokens
            else:
                buffer.append(sentence)
                buffer_tokens += sent_tokens
        
        if buffer:
            chunks.append(self._create_chunk(
                " ".join(buffer),
                [],
                None,
                base_metadata
            ))
        
        return chunks
    
    def _split_large_text(
        self,
        text: str,
        page_numbers: List[int],
        section: Optional[str],
        base_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Split oversized text into chunks."""
        sentences = self._split_sentences(text)
        chunks = []
        buffer = []
        buffer_tokens = 0
        
        for sentence in sentences:
            sent_tokens = count_tokens(sentence)
            
            if buffer_tokens + sent_tokens > self.config.max_tokens:
                if buffer:
                    chunks.append(self._create_chunk(
                        " ".join(buffer),
                        page_numbers,
                        section,
                        base_metadata
                    ))
                buffer = [sentence]
                buffer_tokens = sent_tokens
            else:
                buffer.append(sentence)
                buffer_tokens += sent_tokens
        
        if buffer:
            chunks.append(self._create_chunk(
                " ".join(buffer),
                page_numbers,
                section,
                base_metadata
            ))
        
        return chunks
    
    def _create_chunk(
        self,
        text: str,
        page_numbers: List[int],
        section: Optional[str],
        base_metadata: Dict[str, Any]
    ) -> Chunk:
        """Create a chunk with metadata."""
        content = text
        if section:
            content = f"[Section: {section}]\n\n{text}"
        
        # Page range for citation
        if page_numbers:
            if len(page_numbers) == 1:
                page_ref = f"Page {page_numbers[0]}"
            else:
                page_ref = f"Pages {page_numbers[0]}-{page_numbers[-1]}"
        else:
            page_ref = None
        
        chunk_metadata = self._merge_metadata(base_metadata, {
            "chunk_type": "pdf",
            "page_numbers": page_numbers,
            "page_range": page_ref,
            "section": section,
        })
        
        return Chunk(
            content=content,
            metadata=chunk_metadata,
            token_count=count_tokens(content)
        )
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


# Factory function
def get_pdf_chunker(config: Optional[ChunkingConfig] = None) -> PDFChunker:
    return PDFChunker(config)

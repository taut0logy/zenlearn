"""
Context Assembler - Build citation-aware LLM context.

Assembles retrieved chunks into optimal context for LLM generation
with deduplication, ordering, and citation tracking.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .query_processor import ProcessedQuery
from .reranker import RankedResult


@dataclass
class Citation:
    """Citation information for a chunk."""
    key: str  # e.g., "[1]"
    id: str
    source_file: str
    document_title: str
    location: Optional[str] = None
    location_type: Optional[str] = None  # "slide", "page", "code"
    function_name: Optional[str] = None


@dataclass 
class RetrievedContext:
    """Final context ready for LLM generation."""
    chunks: List[RankedResult]
    total_tokens: int
    citations: List[Citation]
    context_string: str
    query: ProcessedQuery


class ContextAssembler:
    """
    Assembles retrieved chunks into optimal LLM context.
    
    Responsibilities:
    1. Deduplicate overlapping content
    2. Order for coherence (group by source)
    3. Add citation markers
    4. Fit within token budget
    """
    
    def __init__(self, max_tokens: int = 6000):
        self.max_tokens = max_tokens
    
    def assemble(
        self,
        reranked_docs: List[RankedResult],
        query: ProcessedQuery
    ) -> RetrievedContext:
        """
        Assemble final context from reranked documents.
        """
        # Step 1: Deduplicate
        deduped = self._deduplicate(reranked_docs)
        
        # Step 2: Group by source for coherence
        grouped = self._group_by_source(deduped)
        
        # Step 3: Build context with citations
        context_parts = []
        citations = []
        total_tokens = 0
        included_chunks = []
        citation_num = 1
        
        for source_group in grouped:
            for doc in source_group:
                # Check token budget
                doc_tokens = self._count_tokens(doc.content)
                if total_tokens + doc_tokens > self.max_tokens:
                    break
                
                # Create citation
                citation = self._create_citation(doc, citation_num)
                citations.append(citation)
                citation_num += 1
                
                # Format chunk with citation marker
                formatted = self._format_chunk(doc, citation)
                context_parts.append(formatted)
                included_chunks.append(doc)
                
                total_tokens += doc_tokens
        
        # Build final context string
        context_string = self._build_context_string(context_parts, query)
        
        return RetrievedContext(
            chunks=included_chunks,
            total_tokens=total_tokens,
            citations=citations,
            context_string=context_string,
            query=query
        )
    
    def _deduplicate(self, docs: List[RankedResult]) -> List[RankedResult]:
        """Remove duplicate or highly overlapping chunks."""
        seen_fingerprints = set()
        deduped = []
        
        for doc in docs:
            fingerprint = self._create_fingerprint(doc.content)
            if fingerprint not in seen_fingerprints:
                seen_fingerprints.add(fingerprint)
                deduped.append(doc)
        
        return deduped
    
    def _create_fingerprint(self, content: str) -> int:
        """Create content fingerprint for deduplication."""
        # Normalize and hash first 500 chars
        normalized = " ".join(content.lower().split())[:500]
        return hash(normalized)
    
    def _group_by_source(self, docs: List[RankedResult]) -> List[List[RankedResult]]:
        """Group documents by source file for coherent presentation."""
        groups = defaultdict(list)
        
        for doc in docs:
            source = doc.metadata.get('source_file', 'unknown')
            groups[source].append(doc)
        
        # Sort groups by average relevance score
        sorted_groups = sorted(
            groups.values(),
            key=lambda g: sum(d.relevance_score for d in g) / len(g),
            reverse=True
        )
        
        return sorted_groups
    
    def _create_citation(self, doc: RankedResult, num: int) -> Citation:
        """Create citation info for a document chunk."""
        meta = doc.metadata
        
        # Determine location
        location = None
        location_type = None
        function_name = None
        
        if slide := meta.get('slide_number'):
            location = f"Slide {slide}"
            location_type = "slide"
        elif page_range := meta.get('page_range'):
            location = page_range
            location_type = "page"
        elif page := meta.get('page_numbers'):
            if isinstance(page, list) and page:
                location = f"Page {page[0]}" if len(page) == 1 else f"Pages {page[0]}-{page[-1]}"
            location_type = "page"
        elif line_start := meta.get('line_start'):
            location = f"Lines {line_start}-{meta.get('line_end', line_start)}"
            location_type = "code"
            function_name = meta.get('unit_name') or meta.get('function_name')
        
        return Citation(
            key=f"[{num}]",
            id=doc.id,
            source_file=meta.get('source_file', 'Unknown'),
            document_title=meta.get('document_title', meta.get('filename', meta.get('source_file', 'Unknown'))),
            location=location,
            location_type=location_type,
            function_name=function_name
        )
    
    def _format_chunk(self, doc: RankedResult, citation: Citation) -> str:
        """Format chunk with citation marker for LLM context."""
        meta = doc.metadata
        
        # Build header
        header_parts = [f"Source: {citation.document_title}"]
        if citation.location:
            header_parts.append(citation.location)
        if section := meta.get('section'):
            header_parts.append(f"Section: {section}")
        if citation.function_name:
            header_parts.append(f"Function: {citation.function_name}")
        
        header = " | ".join(header_parts)
        
        return f"""
<context citation="{citation.key}">
[{header}]

{doc.content}
</context>
"""
    
    def _build_context_string(
        self,
        parts: List[str],
        query: ProcessedQuery
    ) -> str:
        """Build the final context string for LLM."""
        intro = f"""The following context is retrieved from course materials to help answer the query.
Each section is marked with a citation key that should be referenced in the answer.

Query: {query.original}
Query Type: {query.intent.value}

Retrieved Context:
"""
        return intro + "\n".join(parts)
    
    def _count_tokens(self, text: str) -> int:
        """Approximate token count (1 token ≈ 4 characters)."""
        return len(text) // 4


# Factory
def get_context_assembler(max_tokens: int = 6000) -> ContextAssembler:
    """Create a context assembler instance."""
    return ContextAssembler(max_tokens)

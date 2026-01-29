"""
Semantic Search Service - File-level semantic search.

Provides intelligent file discovery beyond Q&A:
- Search by natural language description
- Return file names with citations
- Semantic understanding of content
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from services.vector_store_service import VectorStoreService, get_vector_store
from services.embedding_service import get_embedding_service
from rag_engine.retriever.hybrid_retriever import SimpleBM25, RetrievalResult
from utils.logger import logger


@dataclass
class FileSearchResult:
    """Result from semantic file search."""

    filename: str
    filepath: str
    file_type: str
    relevance_score: float
    matching_sections: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "filepath": self.filepath,
            "file_type": self.file_type,
            "relevance_score": round(self.relevance_score, 3),
            "matching_sections": self.matching_sections,
            "summary": self.summary,
        }


@dataclass
class SectionMatch:
    """A matching section within a file."""

    content_preview: str
    location: str  # "Slide 5", "Page 3", "Lines 10-20"
    location_type: str  # "slide", "page", "code"
    score: float


class SemanticSearchService:
    """
    Semantic file search for intelligent content discovery.

    Unlike RAG QnA, this focuses on finding relevant files
    and returning structured results with citations.

    Usage:
        search = SemanticSearchService()
        results = await search.search_files("neural network implementation")
        for r in results:
            print(f"{r.filename} - {r.matching_sections}")
    """

    def __init__(
        self,
        collection_name: str = "zenlearn",
        vector_store: Optional[VectorStoreService] = None,
    ):
        self.vector_store = vector_store or get_vector_store(collection_name)
        self.embedding_service = get_embedding_service()
        self._bm25 = None
        self._bm25_docs = None

    async def search_files(
        self,
        query: str,
        top_k: int = 10,
        file_type: Optional[str] = None,
        return_sections: bool = True,
        max_sections_per_file: int = 3,
    ) -> List[FileSearchResult]:
        """
        Search for files matching the query.

        Args:
            query: Natural language search query
            top_k: Maximum number of files to return
            file_type: Optional filter by type ('pdf', 'pptx', 'code')
            return_sections: Include matching sections in results
            max_sections_per_file: Max sections per file

        Returns:
            List of FileSearchResult with files and matching sections
        """
        logger.info(
            f"[SemanticSearch] search_files called: query='{query}', top_k={top_k}, file_type={file_type}"
        )

        # Get chunk-level results
        logger.debug(f"[SemanticSearch] Searching chunks...")
        chunk_results = await self._search_chunks(query, k=50, file_type=file_type)

        logger.info(f"[SemanticSearch] Got {len(chunk_results)} chunk results")

        if not chunk_results:
            logger.warning(
                f"[SemanticSearch] No chunk results found for query: '{query}'"
            )
            return []

        # Group by file
        file_groups = self._group_by_file(chunk_results)
        logger.debug(f"[SemanticSearch] Grouped into {len(file_groups)} files")

        # Build file results
        results = []
        for filepath, chunks in file_groups.items():
            # Calculate file-level score:
            # Use max of top-3 weighted scores (prioritize quality over quantity)
            # This prevents files with many low-relevance chunks from ranking higher
            top_scores = [c.score for c in chunks[:3]]
            file_score = max(top_scores) if top_scores else 0

            # Small boost for files with multiple high-quality matches
            if len(top_scores) >= 2 and top_scores[1] > 0.3:
                file_score *= 1.1
            if len(top_scores) >= 3 and top_scores[2] > 0.3:
                file_score *= 1.05

            # Get file info
            first_chunk = chunks[0]
            metadata = first_chunk.metadata

            # Build matching sections
            sections = []
            if return_sections:
                for chunk in chunks[:max_sections_per_file]:
                    section = self._extract_section_info(chunk)
                    if section:
                        sections.append(section)

            result = FileSearchResult(
                filename=metadata.get("filename", Path(filepath).name),
                filepath=filepath,
                file_type=self._get_file_type(metadata),
                relevance_score=file_score,
                matching_sections=sections,
                summary=self._generate_match_summary(chunks[:3]),
            )
            results.append(result)
            logger.debug(
                f"[SemanticSearch] File: {result.filename}, score={file_score:.3f}, sections={len(sections)}"
            )

        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        final_results = results[:top_k]

        logger.info(f"[SemanticSearch] Returning {len(final_results)} file results")
        return final_results

    async def search_by_content_type(
        self, query: str, content_type: str, top_k: int = 5
    ) -> List[FileSearchResult]:
        """
        Search within a specific content type.

        Args:
            query: Search query
            content_type: 'slides', 'pdf', or 'code'
            top_k: Max results
        """
        type_map = {
            "slides": "pptx",
            "presentations": "pptx",
            "pdf": "pdf",
            "documents": "pdf",
            "code": "code",
        }
        file_type = type_map.get(content_type.lower(), content_type)
        return await self.search_files(query, top_k, file_type=file_type)

    async def find_similar_files(
        self, source_file: str, top_k: int = 5
    ) -> List[FileSearchResult]:
        """
        Find files similar to a given file.

        Args:
            source_file: Path to source file
            top_k: Max similar files to return
        """
        # Get chunks from source file
        source_chunks = self.vector_store.get_by_filter(
            {"source_file": source_file}, limit=10
        )

        if not source_chunks:
            return []

        # Use content as query
        combined_content = " ".join(c["content"][:200] for c in source_chunks[:3])

        # Search but exclude source file
        results = await self.search_files(combined_content, top_k=top_k + 1)

        # Filter out source file
        return [r for r in results if r.filepath != source_file][:top_k]

    async def _search_chunks(
        self, query: str, k: int = 50, file_type: Optional[str] = None
    ) -> List[RetrievalResult]:
        """Dense + sparse search at chunk level."""
        results = {}

        # Dense search
        try:
            where_filter = None
            if file_type:
                where_filter = {"file_type": {"$eq": f".{file_type}"}}

            dense_results = self.vector_store.search(
                query=query, k=k, where=where_filter
            )

            for r in dense_results:
                doc_id = r["id"]
                score = 1 / (1 + r.get("distance", 0))
                results[doc_id] = RetrievalResult(
                    id=doc_id,
                    content=r["content"],
                    metadata=r.get("metadata", {}),
                    score=score,
                    source="dense",
                )
        except Exception as e:
            logger.warning(f"Dense search failed: {e}")

        # BM25 sparse search
        try:
            if self._bm25 is None:
                self._build_bm25_index()

            if self._bm25_docs:
                bm25_results = self._bm25.search(query, k=k)
                for idx, score in bm25_results:
                    doc = self._bm25_docs[idx]
                    doc_id = doc["id"]

                    # Combine scores if already exists
                    if doc_id in results:
                        results[doc_id].score = (results[doc_id].score + score) / 2
                    else:
                        results[doc_id] = RetrievalResult(
                            id=doc_id,
                            content=doc["content"],
                            metadata=doc.get("metadata", {}),
                            score=score,
                            source="sparse",
                        )
        except Exception as e:
            logger.warning(f"Sparse search failed: {e}")

        # Sort and return
        sorted_results = sorted(results.values(), key=lambda x: x.score, reverse=True)
        return sorted_results[:k]

    def _build_bm25_index(self):
        """Build BM25 index from documents."""
        try:
            all_docs = self.vector_store.get_all()
            if all_docs:
                self._bm25_docs = all_docs
                self._bm25 = SimpleBM25()
                self._bm25.fit(all_docs)
                logger.info(f"Built BM25 index with {len(all_docs)} documents")
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            self._bm25_docs = []
            self._bm25 = SimpleBM25()

    def _group_by_file(
        self, results: List[RetrievalResult]
    ) -> Dict[str, List[RetrievalResult]]:
        """Group chunk results by source file."""
        groups = {}
        for r in results:
            filepath = r.metadata.get("source_file", "unknown")
            if filepath not in groups:
                groups[filepath] = []
            groups[filepath].append(r)

        # Sort chunks within each file by score
        for filepath in groups:
            groups[filepath].sort(key=lambda x: x.score, reverse=True)

        return groups

    def _extract_section_info(self, chunk: RetrievalResult) -> Optional[Dict]:
        """Extract section/citation info from chunk."""
        meta = chunk.metadata

        location = None
        location_type = None

        if slide_range := meta.get("slide_range"):
            location = slide_range
            location_type = "slide"
        elif page_range := meta.get("page_range"):
            location = page_range
            location_type = "page"
        elif line_start := meta.get("line_start"):
            location = f"Lines {line_start}-{meta.get('line_end', line_start)}"
            location_type = "code"
        elif unit_name := meta.get("unit_name"):
            location = f"Function: {unit_name}"
            location_type = "code"

        if not location:
            return None

        return {
            "content_preview": chunk.content[:200] + "...",
            "location": location,
            "location_type": location_type,
            "score": round(chunk.score, 3),
            "section": meta.get("section"),
            "titles": meta.get("titles", []),
        }

    def _get_file_type(self, metadata: Dict) -> str:
        """Get human-readable file type."""
        file_type = metadata.get("file_type", "")
        chunk_type = metadata.get("chunk_type", "")

        type_names = {
            ".pptx": "PowerPoint",
            ".ppt": "PowerPoint",
            ".pdf": "PDF Document",
            ".py": "Python Code",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            "slides": "Slides",
            "code": "Code",
        }

        return type_names.get(file_type, type_names.get(chunk_type, "Document"))

    def _generate_match_summary(self, chunks: List[RetrievalResult]) -> str:
        """Generate a brief summary of why this file matched."""
        if not chunks:
            return ""

        sections = []
        for c in chunks:
            if loc := c.metadata.get("slide_range") or c.metadata.get("page_range"):
                sections.append(loc)
            elif title := (c.metadata.get("titles") or [None])[0]:
                sections.append(title)

        if sections:
            return f"Matches in: {', '.join(sections[:3])}"
        return f"Found in {len(chunks)} sections"

    def invalidate_cache(self):
        """Clear BM25 cache."""
        self._bm25 = None
        self._bm25_docs = None


# Factory
def get_semantic_search(collection_name: str = "zenlearn") -> SemanticSearchService:
    """Create a semantic search service instance."""
    return SemanticSearchService(collection_name)

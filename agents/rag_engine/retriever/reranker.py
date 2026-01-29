"""
Reranker - Cohere cross-encoder reranking for precision.

Uses Cohere Rerank API to score query-document pairs more
accurately than embedding similarity alone.
"""

import cohere
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from config.settings import settings
from utils.logger import logger

from .query_processor import ProcessedQuery, QueryIntent
from .hybrid_retriever import RetrievalResult


@dataclass
class RankedResult:
    """Result after reranking."""
    id: str
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    original_rank: int


class Reranker:
    """
    Cross-encoder reranking using Cohere Rerank API.
    
    Scores query-document pairs more accurately than
    bi-encoder similarity (embeddings).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = cohere.Client(api_key or settings.COHERE_API_KEY)
        self.model = "rerank-v3.5"
    
    async def rerank(
        self,
        query: str,
        documents: List[RetrievalResult],
        top_k: int = 10,
        relevance_threshold: float = 0.1
    ) -> List[RankedResult]:
        """
        Rerank documents using Cohere cross-encoder.
        
        Args:
            query: Original user query
            documents: Retrieved documents
            top_k: Number of results to return
            relevance_threshold: Minimum relevance score
            
        Returns:
            Reranked documents with relevance scores
        """
        if not documents:
            return []
        
        try:
            # Prepare document texts
            doc_texts = []
            for doc in documents:
                text = self._prepare_rerank_text(doc)
                doc_texts.append(text)
            
            # Call Cohere Rerank
            response = self.client.rerank(
                query=query,
                documents=doc_texts,
                top_n=min(top_k, len(documents)),
                model=self.model,
                return_documents=False
            )
            
            # Build reranked results
            reranked = []
            for result in response.results:
                if result.relevance_score >= relevance_threshold:
                    doc = documents[result.index]
                    reranked.append(RankedResult(
                        id=doc.id,
                        content=doc.content,
                        metadata=doc.metadata,
                        relevance_score=result.relevance_score,
                        original_rank=result.index
                    ))
            
            logger.info(f"Reranked {len(documents)} docs → {len(reranked)} above threshold")
            return reranked
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return top-k without reranking
            return [
                RankedResult(
                    id=doc.id,
                    content=doc.content,
                    metadata=doc.metadata,
                    relevance_score=doc.score,
                    original_rank=i
                )
                for i, doc in enumerate(documents[:top_k])
            ]
    
    def _prepare_rerank_text(self, doc: RetrievalResult) -> str:
        """Prepare document text for reranking."""
        parts = []
        meta = doc.metadata
        
        # Add title/summary if available
        if title := meta.get('title'):
            parts.append(f"Title: {title}")
        if summary := meta.get('summary'):
            parts.append(f"Summary: {summary}")
        if purpose := meta.get('purpose_summary'):
            parts.append(f"Purpose: {purpose}")
        
        # Main content
        parts.append(doc.content)
        
        return "\n".join(parts)


class AdaptiveReranker(Reranker):
    """
    Adaptive reranking that adjusts strategy based on query type.
    """
    
    # Relevance thresholds by intent
    THRESHOLDS = {
        QueryIntent.FACTUAL: 0.3,
        QueryIntent.CONCEPTUAL: 0.2,
        QueryIntent.CODE_FIND: 0.25,
        QueryIntent.CODE_EXPLAIN: 0.2,
        QueryIntent.COMPARE: 0.15,
        QueryIntent.EXAMPLE: 0.2,
        QueryIntent.EXERCISE: 0.2,
    }
    
    async def rerank_adaptive(
        self,
        processed_query: ProcessedQuery,
        documents: List[RetrievalResult],
        top_k: int = 10
    ) -> List[RankedResult]:
        """
        Rerank with query-aware adjustments.
        """
        # Get threshold for this intent
        threshold = self.THRESHOLDS.get(processed_query.intent, 0.2)
        
        # Boost code results for code queries
        if processed_query.is_code_query:
            documents = self._boost_code_results(documents)
        
        return await self.rerank(
            query=processed_query.original,
            documents=documents,
            top_k=top_k,
            relevance_threshold=threshold
        )
    
    def _boost_code_results(
        self,
        documents: List[RetrievalResult],
        boost_factor: float = 1.2
    ) -> List[RetrievalResult]:
        """Boost code documents for code-focused queries."""
        boosted = []
        
        for doc in documents:
            if doc.metadata.get('chunk_type') == 'code':
                # Create boosted copy
                boosted.append(RetrievalResult(
                    id=doc.id,
                    content=doc.content,
                    metadata=doc.metadata,
                    score=doc.score * boost_factor,
                    source=doc.source
                ))
            else:
                boosted.append(doc)
        
        # Re-sort by boosted score
        boosted.sort(key=lambda x: x.score, reverse=True)
        return boosted


# Factory
def get_reranker(adaptive: bool = True) -> Reranker:
    """Create a reranker instance."""
    if adaptive:
        return AdaptiveReranker()
    return Reranker()

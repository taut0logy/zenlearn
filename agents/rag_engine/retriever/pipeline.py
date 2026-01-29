"""
Retrieval Pipeline - Complete retrieval from query to context.

Orchestrates query processing, hybrid retrieval, reranking,
and context assembly into a single pipeline.
"""

from typing import Optional, Dict, Any

from services.gemini_service import GeminiService
from utils.logger import logger

from .query_processor import QueryProcessor, ProcessedQuery, get_query_processor
from .hybrid_retriever import HybridRetriever, get_hybrid_retriever
from .reranker import AdaptiveReranker, get_reranker
from .context_assembler import ContextAssembler, RetrievedContext, get_context_assembler


class RetrievalPipeline:
    """
    Complete retrieval pipeline from query to context.
    
    Stages:
    1. Query Processing - Understand intent, expand queries
    2. Hybrid Retrieval - Dense + sparse search with RRF fusion
    3. Reranking - Cross-encoder precision optimization
    4. Context Assembly - Build citation-aware LLM context
    
    Usage:
        pipeline = RetrievalPipeline()
        context = await pipeline.retrieve("How does quicksort work?")
    """
    
    def __init__(
        self,
        collection_name: str = "zenlearn",
        llm_service: Optional[GeminiService] = None,
        max_context_tokens: int = 6000
    ):
        self.query_processor = get_query_processor(llm_service)
        self.retriever = get_hybrid_retriever(collection_name)
        self.reranker = get_reranker(adaptive=True)
        self.assembler = get_context_assembler(max_context_tokens)
    
    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        skip_rerank: bool = False
    ) -> RetrievedContext:
        """
        Full retrieval pipeline.
        
        Args:
            query: User query string
            filters: Optional filters (course_id, category, etc.)
            top_k: Number of final chunks
            skip_rerank: If True, skip Cohere reranking (faster, less precise)
            
        Returns:
            RetrievedContext ready for generation
        """
        logger.info(f"Starting retrieval for: {query[:100]}...")
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 1: Query Processing
        # ═══════════════════════════════════════════════════════════
        
        processed = await self.query_processor.process(query)
        logger.info(f"Query intent: {processed.intent.value}, entities: {processed.entities}")
        
        # Merge explicit filters
        if filters:
            processed.filters.update(filters)
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 2: Hybrid Retrieval
        # ═══════════════════════════════════════════════════════════
        
        candidates = await self.retriever.retrieve(
            processed_query=processed,
            k=50  # Over-retrieve for reranking
        )
        
        logger.info(f"Retrieved {len(candidates)} candidates")
        
        if not candidates:
            logger.warning("No candidates retrieved")
            return RetrievedContext(
                chunks=[],
                total_tokens=0,
                citations=[],
                context_string="No relevant context found.",
                query=processed
            )
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 3: Reranking
        # ═══════════════════════════════════════════════════════════
        
        if skip_rerank:
            # Convert to RankedResult format without reranking
            from .reranker import RankedResult
            reranked = [
                RankedResult(
                    id=c.id,
                    content=c.content,
                    metadata=c.metadata,
                    relevance_score=c.score,
                    original_rank=i
                )
                for i, c in enumerate(candidates[:top_k])
            ]
        else:
            reranked = await self.reranker.rerank_adaptive(
                processed_query=processed,
                documents=candidates,
                top_k=top_k
            )
        
        logger.info(f"Reranked to {len(reranked)} documents")
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 4: Context Assembly
        # ═══════════════════════════════════════════════════════════
        
        context = self.assembler.assemble(
            reranked_docs=reranked,
            query=processed
        )
        
        logger.info(f"Assembled context: {context.total_tokens} tokens, {len(context.citations)} citations")
        
        return context
    
    async def retrieve_simple(
        self,
        query: str,
        k: int = 5
    ) -> str:
        """
        Simplified retrieval returning just context string.
        
        Use for quick testing or simple QA.
        """
        context = await self.retrieve(query, top_k=k)
        return context.context_string
    
    def invalidate_cache(self):
        """Invalidate retriever caches (e.g., BM25 index)."""
        self.retriever.invalidate_bm25_cache()


# Factory and singleton
_pipeline_instance = None

def get_retrieval_pipeline(
    collection_name: str = "zenlearn",
    **kwargs
) -> RetrievalPipeline:
    """Get or create a retrieval pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RetrievalPipeline(collection_name, **kwargs)
    return _pipeline_instance


def reset_pipeline():
    """Reset the singleton pipeline instance."""
    global _pipeline_instance
    _pipeline_instance = None

"""
Retriever Module - Hybrid search with reranking.

Provides complete retrieval pipeline from query to context.
"""

from .query_processor import (
    QueryProcessor,
    ProcessedQuery,
    QueryIntent,
    get_query_processor,
)

from .hybrid_retriever import (
    HybridRetriever,
    RetrievalResult,
    SimpleBM25,
    get_hybrid_retriever,
)

from .reranker import (
    Reranker,
    AdaptiveReranker,
    RankedResult,
    get_reranker,
)

from .context_assembler import (
    ContextAssembler,
    RetrievedContext,
    Citation,
    get_context_assembler,
)

from .pipeline import (
    RetrievalPipeline,
    get_retrieval_pipeline,
    reset_pipeline,
)


__all__ = [
    # Query processing
    'QueryProcessor',
    'ProcessedQuery',
    'QueryIntent',
    'get_query_processor',
    
    # Hybrid retrieval
    'HybridRetriever',
    'RetrievalResult',
    'SimpleBM25',
    'get_hybrid_retriever',
    
    # Reranking
    'Reranker',
    'AdaptiveReranker',
    'RankedResult',
    'get_reranker',
    
    # Context assembly
    'ContextAssembler',
    'RetrievedContext',
    'Citation',
    'get_context_assembler',
    
    # Pipeline
    'RetrievalPipeline',
    'get_retrieval_pipeline',
    'reset_pipeline',
]

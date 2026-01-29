"""
RAG Engine - Core retrieval-augmented generation components.

Modules:
    - code_processor: LLM-assisted code analysis
    - chunker: Content-aware document chunking
    - retriever: Hybrid search and reranking
    - ingestion_service: File processing and storage
    - semantic_search: File-level intelligent search
"""

from rag_engine.code_processor import (
    CodePreprocessor,
    get_code_preprocessor,
    CodeAnalysisResult,
    StaticAnalyzer,
    static_analyzer,
)
from rag_engine.chunker import (
    ChunkingService,
    get_chunking_service,
    chunking_service,
    Chunk,
    ChunkingConfig,
)
from rag_engine.retriever import (
    RetrievalPipeline,
    get_retrieval_pipeline,
    QueryProcessor,
    ProcessedQuery,
    QueryIntent,
    HybridRetriever,
    Reranker,
    AdaptiveReranker,
    ContextAssembler,
    RetrievedContext,
)
from rag_engine.ingestion_service import (
    IngestionService,
    get_ingestion_service,
)
from rag_engine.semantic_search import (
    SemanticSearchService,
    FileSearchResult,
    get_semantic_search,
)

__all__ = [
    # Code processor
    'CodePreprocessor',
    'get_code_preprocessor',
    'CodeAnalysisResult',
    'StaticAnalyzer',
    'static_analyzer',
    
    # Chunker
    'ChunkingService',
    'get_chunking_service',
    'chunking_service',
    'Chunk',
    'ChunkingConfig',
    
    # Retriever
    'RetrievalPipeline',
    'get_retrieval_pipeline',
    'QueryProcessor',
    'ProcessedQuery',
    'QueryIntent',
    'HybridRetriever',
    'Reranker',
    'AdaptiveReranker',
    'ContextAssembler',
    'RetrievedContext',
    
    # Ingestion
    'IngestionService',
    'get_ingestion_service',
    
    # Semantic Search
    'SemanticSearchService',
    'FileSearchResult',
    'get_semantic_search',
]


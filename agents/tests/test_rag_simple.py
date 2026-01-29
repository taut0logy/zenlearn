"""
Simple RAG Engine Test - Local Testing.

Tests the RAG engine components without requiring cloud APIs.
Uses local ChromaDB for quick testing.

Usage:
    cd agents
    python -m tests.test_rag_simple
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Use local ChromaDB for testing
import chromadb
LOCAL_CLIENT = chromadb.PersistentClient(path="./test_chroma_db")


def get_local_collection(name: str = "test-collection"):
    """Get a local ChromaDB collection for testing."""
    return LOCAL_CLIENT.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )


def test_chunking():
    """Test chunking service with sample files."""
    print("\n" + "="*60)
    print("TEST: Chunking Service")
    print("="*60)
    
    from rag_engine.chunker import get_chunking_service
    
    service = get_chunking_service()
    contents_dir = Path(__file__).parent.parent / "contents"
    
    print(f"Supported extensions: {service.get_supported_extensions()}")
    
    for file_path in contents_dir.glob("*"):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            
            # Check if extension is supported
            all_exts = set()
            for exts in service.get_supported_extensions().values():
                all_exts.update(exts)
            
            if ext in all_exts:
                try:
                    chunks = service.chunk_file(str(file_path), {"source": file_path.name})
                    print(f"\n{file_path.name}: {len(chunks)} chunks")
                    for i, chunk in enumerate(chunks[:2]):
                        print(f"  Chunk {i+1}: {chunk.token_count} tokens")
                        print(f"    {chunk.content[:100]}...")
                except Exception as e:
                    print(f"\n{file_path.name}: ERROR - {e}")
            else:
                print(f"\n{file_path.name}: Skipped (unsupported)")


def test_bm25_search():
    """Test BM25 sparse search (no API needed)."""
    print("\n" + "="*60)
    print("TEST: BM25 Search (No API)")
    print("="*60)
    
    from rag_engine.retriever.hybrid_retriever import SimpleBM25
    
    # Sample documents
    docs = [
        {"id": "1", "content": "HTTP/2 is a major revision of HTTP that improves web performance", "metadata": {"type": "slide"}},
        {"id": "2", "content": "Web caching stores copies of resources to reduce latency", "metadata": {"type": "slide"}},
        {"id": "3", "content": "CNN and GRU models are used for text classification", "metadata": {"type": "code"}},
        {"id": "4", "content": "Hate speech detection using neural networks and deep learning", "metadata": {"type": "code"}},
        {"id": "5", "content": "The hackathon focuses on building AI-powered applications", "metadata": {"type": "pdf"}},
    ]
    
    bm25 = SimpleBM25()
    bm25.fit(docs)
    
    queries = [
        "How does HTTP/2 work?",
        "CNN text classification",
        "hackathon AI",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = bm25.search(query, k=3)
        for idx, score in results:
            print(f"  Score {score:.3f}: {docs[idx]['content'][:50]}...")


def test_query_processor_local():
    """Test query processor with mock LLM."""
    print("\n" + "="*60)
    print("TEST: Query Processor (local)")
    print("="*60)
    
    from rag_engine.retriever.query_processor import ProcessedQuery, QueryIntent
    
    # Create a mock processed query
    query = "How does HTTP/2 improve web performance?"
    
    # Simulate processing
    processed = ProcessedQuery(
        original=query,
        intent=QueryIntent.CONCEPTUAL,
        entities=["HTTP/2", "web performance"],
        filters={},
        expanded_queries=[
            query,
            "HTTP/2 performance improvements",
            "HTTP/2 features",
        ],
        is_code_query=False
    )
    
    print(f"Query: {processed.original}")
    print(f"Intent: {processed.intent.value}")
    print(f"Entities: {processed.entities}")
    print(f"Expanded: {processed.expanded_queries}")


def test_context_assembly():
    """Test context assembly."""
    print("\n" + "="*60)
    print("TEST: Context Assembly")
    print("="*60)
    
    from rag_engine.retriever.context_assembler import ContextAssembler
    from rag_engine.retriever.reranker import RankedResult
    from rag_engine.retriever.query_processor import ProcessedQuery, QueryIntent
    
    assembler = ContextAssembler(max_tokens=2000)
    
    # Mock documents
    docs = [
        RankedResult(
            id="doc1",
            content="HTTP/2 uses binary framing for more efficient parsing...",
            metadata={"filename": "lecture.pptx", "slide_number": 5},
            relevance_score=0.85,
            original_rank=0
        ),
        RankedResult(
            id="doc2",
            content="Web caching reduces latency by storing responses...",
            metadata={"filename": "lecture.pptx", "slide_number": 10},
            relevance_score=0.72,
            original_rank=1
        ),
    ]
    
    query = ProcessedQuery(
        original="How does HTTP/2 work?",
        intent=QueryIntent.CONCEPTUAL,
        entities=["HTTP/2"],
    )
    
    context = assembler.assemble(docs, query)
    
    print(f"Total tokens: {context.total_tokens}")
    print(f"Citations: {len(context.citations)}")
    for c in context.citations:
        print(f"  {c.key} - {c.document_title} ({c.location})")
    
    print(f"\nContext preview:\n{context.context_string[:500]}...")


async def test_full_pipeline_mock():
    """Test pipeline with mocked services."""
    print("\n" + "="*60)
    print("TEST: Full Pipeline (with real APIs)")
    print("="*60)
    
    try:
        from rag_engine.ingestion_service import get_ingestion_service
        from rag_engine.retriever import get_retrieval_pipeline, reset_pipeline
        
        contents_dir = Path(__file__).parent.parent / "contents"
        
        # Ingest
        print("Ingesting files...")
        ingestion = get_ingestion_service("zenlearn-simple-test")
        ingestion.clear_collection()
        
        results = ingestion.ingest_directory(str(contents_dir))
        total = sum(len(ids) for ids in results.values())
        print(f"Ingested {total} chunks from {len(results)} files")
        
        # Retrieve
        print("\nTesting retrieval...")
        reset_pipeline()
        pipeline = get_retrieval_pipeline("zenlearn-simple-test")
        
        query = "Explain web caching"
        print(f"Query: {query}")
        
        context = await pipeline.retrieve(query, top_k=3, skip_rerank=True)
        
        print(f"Results: {len(context.chunks)} chunks, {context.total_tokens} tokens")
        for i, chunk in enumerate(context.chunks[:3]):
            print(f"\n  Result {i+1}:")
            print(f"    Source: {chunk.metadata.get('filename', 'unknown')}")
            print(f"    Content: {chunk.content[:100]}...")
            
    except Exception as e:
        print(f"API test failed (expected if no API keys): {e}")


def run_local_tests():
    """Run tests that don't require API keys."""
    print("\n" + "#"*60)
    print("# RAG ENGINE LOCAL TESTS")
    print("#"*60)
    
    test_chunking()
    test_bm25_search()
    test_query_processor_local()
    test_context_assembly()
    
    print("\n" + "#"*60)
    print("# LOCAL TESTS COMPLETE")
    print("#"*60)


async def run_api_tests():
    """Run tests that require API keys."""
    print("\n" + "#"*60)
    print("# RAG ENGINE API TESTS")
    print("#"*60)
    
    await test_full_pipeline_mock()
    
    print("\n" + "#"*60)
    print("# API TESTS COMPLETE")
    print("#"*60)


if __name__ == "__main__":
    run_local_tests()
    
    # Optionally run API tests
    import sys
    if "--api" in sys.argv:
        asyncio.run(run_api_tests())

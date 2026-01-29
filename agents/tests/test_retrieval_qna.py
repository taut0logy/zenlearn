"""
End-to-End QnA Tests for RAG Engine.

Tests the complete retrieval pipeline with real files:
1. Ingest sample files (PDF, PPTX, Python)
2. Run test queries
3. Verify retrieval returns relevant results

Usage:
    cd agents
    python -m tests.test_retrieval_qna
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test queries with expected content matches
TEST_QUERIES = [
    {
        "query": "What is HTTP/2 and how does it improve web performance?",
        "expected_source": "L4_Application_Layer",
        "expected_type": "pptx",
        "description": "Should find HTTP/2 slides from PPTX"
    },
    {
        "query": "Explain web caching and how it works",
        "expected_source": "L4_Application_Layer",
        "expected_type": "pptx",
        "description": "Should find caching slides from PPTX"
    },
    {
        "query": "CNN GRU model for hate speech detection",
        "expected_source": "cnn_gru_hatespeech",
        "expected_type": "py",
        "description": "Should find Python code file"
    },
    {
        "query": "How to build a neural network for text classification",
        "expected_source": "cnn_gru_hatespeech",
        "expected_type": "py",
        "description": "Should find neural network code"
    },
    {
        "query": "What is the hackathon about?",
        "expected_source": "Hackathon",
        "expected_type": "pdf",
        "description": "Should find hackathon PDF content"
    },
]


def test_ingestion():
    """Test file ingestion."""
    print("\n" + "="*60)
    print("TEST: File Ingestion")
    print("="*60)
    
    from rag_engine.ingestion_service import get_ingestion_service
    
    service = get_ingestion_service("zenlearn-test")
    contents_dir = Path(__file__).parent.parent / "contents"
    
    if not contents_dir.exists():
        print(f"ERROR: Contents directory not found: {contents_dir}")
        return None
    
    # Clear existing data
    print("Clearing existing data...")
    service.clear_collection()
    
    # Ingest all files
    print(f"Ingesting files from: {contents_dir}")
    results = service.ingest_directory(str(contents_dir))
    
    for filename, chunk_ids in results.items():
        print(f"  {filename}: {len(chunk_ids)} chunks")
    
    stats = service.get_stats()
    print(f"\nTotal documents: {stats['document_count']}")
    
    return service


async def test_query_processing():
    """Test query processing."""
    print("\n" + "="*60)
    print("TEST: Query Processing")
    print("="*60)
    
    from rag_engine.retriever import get_query_processor
    
    processor = get_query_processor()
    
    for test in TEST_QUERIES[:2]:
        print(f"\nQuery: {test['query']}")
        result = await processor.process(test['query'])
        print(f"  Intent: {result.intent.value}")
        print(f"  Entities: {result.entities[:3]}")
        print(f"  Expanded queries: {len(result.expanded_queries)}")
        if result.hyde_text:
            print(f"  HyDE: {result.hyde_text[:100]}...")


async def test_retrieval_pipeline():
    """Test the full retrieval pipeline."""
    print("\n" + "="*60)
    print("TEST: Retrieval Pipeline")
    print("="*60)
    
    from rag_engine.retriever import get_retrieval_pipeline, reset_pipeline
    
    # Reset to use test collection
    reset_pipeline()
    pipeline = get_retrieval_pipeline("zenlearn-test")
    
    passed = 0
    failed = 0
    
    for test in TEST_QUERIES:
        print(f"\n{'─'*40}")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['expected_source']} ({test['expected_type']})")
        print(f"─"*40)
        
        try:
            context = await pipeline.retrieve(
                test['query'],
                top_k=5,
                skip_rerank=False  # Use reranking for better precision
            )
            
            if context.chunks:
                # Check if expected source is found
                found_expected = False
                for i, chunk in enumerate(context.chunks[:3]):
                    source = chunk.metadata.get('source_file', '')
                    filename = chunk.metadata.get('filename', '')
                    
                    print(f"\n  Result {i+1}:")
                    print(f"    Source: {filename}")
                    print(f"    Score: {chunk.relevance_score:.3f}")
                    print(f"    Content: {chunk.content[:150]}...")
                    
                    if test['expected_source'].lower() in source.lower() or \
                       test['expected_source'].lower() in filename.lower():
                        found_expected = True
                
                if found_expected:
                    print(f"\n  ✅ PASS: Found expected source")
                    passed += 1
                else:
                    print(f"\n  ⚠️ PARTIAL: Source not in top 3")
                    passed += 0.5
            else:
                print(f"\n  ❌ FAIL: No results returned")
                failed += 1
                
        except Exception as e:
            print(f"\n  ❌ ERROR: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{len(TEST_QUERIES)} passed, {failed} failed")
    print(f"{'='*60}")


async def test_context_assembly():
    """Test context assembly with citations."""
    print("\n" + "="*60)
    print("TEST: Context Assembly")
    print("="*60)
    
    from rag_engine.retriever import get_retrieval_pipeline
    
    pipeline = get_retrieval_pipeline("zenlearn-test")
    
    context = await pipeline.retrieve(
        "Explain how HTTP caching works with web servers",
        top_k=5
    )
    
    print(f"\nTotal tokens: {context.total_tokens}")
    print(f"Number of citations: {len(context.citations)}")
    
    print("\nCitations:")
    for citation in context.citations:
        print(f"  {citation.key} - {citation.document_title}")
        if citation.location:
            print(f"    Location: {citation.location}")
    
    print(f"\nContext string preview (first 500 chars):")
    print(context.context_string[:500])


async def run_all_tests():
    """Run all QnA tests."""
    print("\n" + "#"*60)
    print("# RAG ENGINE QnA TEST SUITE")
    print("#"*60)
    
    try:
        # Test ingestion
        service = test_ingestion()
        if not service:
            print("ERROR: Ingestion failed, cannot continue")
            return
        
        # Wait for embeddings to be processed
        print("\nWaiting for embeddings...")
        await asyncio.sleep(2)
        
        # Test query processing
        await test_query_processing()
        
        # Test full retrieval
        await test_retrieval_pipeline()
        
        # Test context assembly
        await test_context_assembly()
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "#"*60)
    print("# TESTS COMPLETE")
    print("#"*60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())

"""
Semantic File Search Test.

Tests the semantic search service for file-level discovery.

Usage:
    cd agents
    python -m tests.test_semantic_search
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_semantic_search():
    """Test semantic file search."""
    print("\n" + "="*60)
    print("TEST: Semantic File Search")
    print("="*60)
    
    from rag_engine.semantic_search import get_semantic_search
    from rag_engine.ingestion_service import get_ingestion_service
    
    contents_dir = Path(__file__).parent.parent / "contents"
    
    # First ingest files
    print("\n1. Ingesting files...")
    ingestion = get_ingestion_service("zenlearn-search-test")
    ingestion.clear_collection()
    
    results = ingestion.ingest_directory(str(contents_dir))
    total = sum(len(ids) for ids in results.values())
    print(f"   Ingested {total} chunks from {len(results)} files")
    
    # Create search service
    search = get_semantic_search("zenlearn-search-test")
    
    # Test queries
    queries = [
        "HTTP/2 performance improvements",
        "neural network hate speech detection",
        "web caching",
        "hackathon AI API",
    ]
    
    print("\n2. Running file searches...")
    for query in queries:
        print(f"\n{'─'*50}")
        print(f"Query: {query}")
        print(f"{'─'*50}")
        
        results = await search.search_files(query, top_k=3)
        
        if not results:
            print("   No files found")
            continue
        
        for i, result in enumerate(results, 1):
            print(f"\n   {i}. {result.filename}")
            print(f"      Type: {result.file_type}")
            print(f"      Score: {result.relevance_score:.3f}")
            print(f"      Summary: {result.summary}")
            
            if result.matching_sections:
                print(f"      Matching sections:")
                for section in result.matching_sections[:2]:
                    print(f"        - {section['location']}: {section['content_preview'][:80]}...")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


def test_search_result_format():
    """Test FileSearchResult structure."""
    print("\n" + "="*60)
    print("TEST: FileSearchResult Format")
    print("="*60)
    
    from rag_engine.semantic_search import FileSearchResult
    
    result = FileSearchResult(
        filename="test.pdf",
        filepath="/path/to/test.pdf",
        file_type="PDF Document",
        relevance_score=0.85,
        matching_sections=[
            {
                "content_preview": "HTTP/2 improves performance...",
                "location": "Page 5",
                "location_type": "page",
                "score": 0.9
            }
        ],
        summary="Matches in: Page 5"
    )
    
    print(f"Filename: {result.filename}")
    print(f"File type: {result.file_type}")
    print(f"Score: {result.relevance_score}")
    print(f"Sections: {len(result.matching_sections)}")
    print(f"Dict format: {result.to_dict()}")
    
    print("\n✅ FileSearchResult format OK")


if __name__ == "__main__":
    test_search_result_format()
    asyncio.run(test_semantic_search())

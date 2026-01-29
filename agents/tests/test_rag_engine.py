"""
Test Script for Code Preprocessor and Chunking System.

Run this file to test the implementation manually.
Usage: python -m tests.test_rag_engine
"""

import asyncio
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


SAMPLE_CODE = '''
def binary_search(arr, target):
    """
    Search for target in a sorted array using binary search.
    
    Args:
        arr: Sorted list of elements
        target: Element to find
        
    Returns:
        Index of target or -1 if not found
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1


def quicksort(arr):
    """
    Sort array using quicksort algorithm.
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)


class Calculator:
    """Simple calculator class."""
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b
'''


def test_static_analyzer():
    """Test static code analysis."""
    print("\n" + "="*60)
    print("TEST: Static Analyzer")
    print("="*60)
    
    from rag_engine.code_processor import static_analyzer
    
    result = static_analyzer.analyze(SAMPLE_CODE, "sample.py")
    
    print(f"Language: {result.language}")
    print(f"Functions found: {[f.name for f in result.functions]}")
    print(f"Classes found: {[c.name for c in result.classes]}")
    print(f"Imports: {result.imports}")
    
    for func in result.functions[:2]:
        print(f"\n  Function: {func.qualified_name}")
        print(f"    Lines: {func.start_line}-{func.end_line}")
        print(f"    Docstring: {func.docstring[:50] if func.docstring else 'None'}...")
    
    return result


def test_code_chunker():
    """Test code chunking without LLM."""
    print("\n" + "="*60)
    print("TEST: Code Chunker (no LLM)")
    print("="*60)
    
    from rag_engine.chunker import get_code_chunker
    
    chunker = get_code_chunker()
    chunks = chunker.chunk(SAMPLE_CODE, {"filename": "sample.py"})
    
    print(f"Total chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"  Type: {chunk.metadata.get('chunk_type')}")
        print(f"  Unit: {chunk.metadata.get('unit_name', 'N/A')}")
        print(f"  Tokens: {chunk.token_count}")
        print(f"  Content preview: {chunk.content[:100]}...")
    
    return chunks


async def test_code_preprocessor():
    """Test full code preprocessing with LLM."""
    print("\n" + "="*60)
    print("TEST: Code Preprocessor (with LLM)")
    print("="*60)
    
    from rag_engine.code_processor import get_code_preprocessor
    
    preprocessor = get_code_preprocessor(max_functions=3)
    
    try:
        result = await preprocessor.process(SAMPLE_CODE, "sample.py")
        
        print(f"Purpose: {result.purpose_summary}")
        print(f"Algorithms: {result.algorithms_used}")
        print(f"Concepts: {result.concepts_demonstrated}")
        print(f"Complexity: {result.complexity}")
        print(f"NL Queries (sample): {result.nl_queries[:3]}")
        
        for name, analysis in list(result.functions.items())[:2]:
            print(f"\nFunction '{name}':")
            print(f"  Summary: {analysis.summary}")
            print(f"  Complexity: {analysis.time_complexity}")
        
        # Test embedding text generation
        embedding_text = preprocessor.to_embedding_text(result)
        print(f"\nEmbedding text preview:\n{embedding_text[:300]}...")
        
        return result
    except Exception as e:
        print(f"Error (may need API key): {e}")
        return None


async def test_chunking_service():
    """Test unified chunking service."""
    print("\n" + "="*60)
    print("TEST: Chunking Service")
    print("="*60)
    
    from rag_engine.chunker import get_chunking_service
    
    service = get_chunking_service()
    
    # Test supported extensions
    print(f"Supported extensions: {service.get_supported_extensions()}")
    
    # Test code chunking
    chunks = service.chunk_content(SAMPLE_CODE, 'code', {"filename": "test.py"})
    print(f"\nCode chunks: {len(chunks)}")
    
    return chunks


def test_embedding_service():
    """Test embedding service."""
    print("\n" + "="*60)
    print("TEST: Embedding Service")
    print("="*60)
    
    try:
        from services.embedding_service import embedding_service
        
        texts = ["Binary search algorithm", "Sort a list in Python"]
        embeddings = embedding_service.embed_documents(texts)
        
        print(f"Embedded {len(embeddings)} texts")
        print(f"Embedding dimension: {len(embeddings[0])}")
        
        query_emb = embedding_service.embed_query("how to search efficiently")
        print(f"Query embedding dimension: {len(query_emb)}")
        
        return embeddings
    except Exception as e:
        print(f"Error (may need API key): {e}")
        return None


def test_vector_store():
    """Test vector store service."""
    print("\n" + "="*60)
    print("TEST: Vector Store Service")
    print("="*60)
    
    try:
        from services.vector_store_service import get_vector_store
        
        store = get_vector_store("test-collection")
        
        # Add test documents
        docs = [
            "Binary search finds elements in O(log n) time",
            "Quicksort is a divide and conquer sorting algorithm",
        ]
        metadatas = [
            {"type": "algorithm", "topic": "search"},
            {"type": "algorithm", "topic": "sort"},
        ]
        
        ids = store.add_documents(docs, metadatas)
        print(f"Added {len(ids)} documents")
        
        # Search
        results = store.search("efficient search", k=2)
        print(f"Search results: {len(results)}")
        for r in results:
            print(f"  Score: {r['score']:.3f} - {r['content'][:50]}...")
        
        # Cleanup
        store.delete(ids)
        print("Cleaned up test documents")
        
        return results
    except Exception as e:
        print(f"Error (may need API key/ChromaDB): {e}")
        return None


async def run_all_tests():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# RAG ENGINE TEST SUITE")
    print("#"*60)
    
    # Static tests (no API needed)
    test_static_analyzer()
    test_code_chunker()
    await test_chunking_service()
    
    # API-dependent tests
    print("\n" + "-"*60)
    print("The following tests require API keys...")
    print("-"*60)
    
    test_embedding_service()
    test_vector_store()
    await test_code_preprocessor()
    
    print("\n" + "#"*60)
    print("# TESTS COMPLETE")
    print("#"*60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())

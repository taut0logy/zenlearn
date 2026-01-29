# 🔍 Retrieval Pipeline - Hybrid Search & Intelligent Reranking

> **Goal**: Maximize retrieval precision while maintaining recall  
> **Key Technique**: Hybrid dense-sparse search with cross-encoder reranking

---

## 📋 Table of Contents

1. [Retrieval Philosophy](#retrieval-philosophy)
2. [Pipeline Architecture](#pipeline-architecture)
3. [Query Processing Agent](#query-processing-agent)
4. [Hybrid Retrieval System](#hybrid-retrieval-system)
5. [Reranking Strategy](#reranking-strategy)
6. [Context Assembly](#context-assembly)
7. [Implementation Guide](#implementation-guide)

---

## 🎯 Retrieval Philosophy

### The Precision-Recall Tradeoff

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL QUALITY DIMENSIONS                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  RECALL: "Did we find all relevant content?"                           │
│  ───────────────────────────────────────────                           │
│  High recall = don't miss anything important                           │
│  Risk: Returns too much irrelevant content                             │
│                                                                         │
│  PRECISION: "Is everything we found relevant?"                         │
│  ─────────────────────────────────────────────                         │
│  High precision = every result is useful                               │
│  Risk: Might miss some relevant content                                │
│                                                                         │
│  OUR STRATEGY: Optimize for BOTH                                       │
│  ────────────────────────────────                                      │
│  Stage 1: HIGH RECALL    → Hybrid search (dense + sparse)              │
│  Stage 2: HIGH PRECISION → Cross-encoder reranking                     │
│  Stage 3: OPTIMAL        → Context assembly with citations             │
│                                                                         │
│  Research shows this 2-stage approach improves accuracy 28-48%         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Retrieval Goals for Learning Platform

| Goal | Strategy | Metric |
|------|----------|--------|
| Find relevant slides | Semantic search on enriched text | Recall@10 > 0.9 |
| Find relevant code | Hybrid search + NL bridge | MRR > 0.7 |
| Precise citations | Page/slide-level tracking | 100% citation accuracy |
| Low latency | Two-stage retrieval | < 2 seconds |
| Reduce hallucination | High-quality context | Groundedness > 0.95 |

---

## 🏗️ Pipeline Architecture

### Complete Retrieval Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       RETRIEVAL PIPELINE                                  │
└──────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │  User Query  │
     │  "How does   │
     │  binary      │
     │  search      │
     │  work?"      │
     └──────┬───────┘
            │
            ▼
┌───────────────────────┐
│  QUERY PROCESSOR      │  ◄── Agentic query understanding
│  (LLM Agent)          │
│  ├─ Classify intent   │      Intent: code_explanation
│  ├─ Extract entities  │      Entities: [binary search, algorithm]
│  ├─ Detect filters    │      Filters: {category: lab}
│  └─ Generate variants │      Variants: ["binary search algorithm", 
│                       │                 "search sorted array", ...]
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  QUERY EXPANDER       │  ◄── Optional HyDE + synonyms
│  ├─ HyDE generation   │      "Binary search divides the search 
│  ├─ Synonym injection │       interval in half..."
│  └─ Multi-query       │
└───────────┬───────────┘
            │
            ├──────────────────────────────────────────────┐
            │                                              │
            ▼                                              ▼
┌───────────────────────┐                    ┌───────────────────────┐
│   DENSE RETRIEVAL     │                    │   SPARSE RETRIEVAL    │
│   (Cohere Embed)      │                    │   (BM25)              │
│                       │                    │                       │
│   ChromaDB semantic   │                    │   Keyword matching    │
│   similarity search   │                    │   on metadata +       │
│   k = 50              │                    │   content, k = 50     │
└───────────┬───────────┘                    └───────────┬───────────┘
            │                                            │
            └──────────────────┬─────────────────────────┘
                               │
                               ▼
                  ┌───────────────────────┐
                  │   RECIPROCAL RANK     │
                  │   FUSION (RRF)        │
                  │                       │
                  │   Combine dense +     │
                  │   sparse results      │
                  │   k = 60              │
                  │   Output: ~30 docs    │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   COHERE RERANK       │  ◄── Cross-encoder precision
                  │                       │
                  │   Score each          │
                  │   query-doc pair      │
                  │                       │
                  │   Output: top 10      │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   CONTEXT ASSEMBLER   │  ◄── Build LLM context
                  │   ├─ Deduplicate      │
                  │   ├─ Order by source  │
                  │   ├─ Add citations    │
                  │   └─ Fit token limit  │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   RETRIEVED CONTEXT   │
                  │   With full citations │
                  │   Ready for LLM       │
                  └───────────────────────┘
```

---

## 🤖 Query Processing Agent

### Intent Classification

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict

class QueryIntent(str, Enum):
    FACTUAL = "factual"              # "What is binary search?"
    CONCEPTUAL = "conceptual"        # "How does binary search work?"
    CODE_FIND = "code_find"          # "Show me binary search code"
    CODE_EXPLAIN = "code_explain"    # "Explain this sorting algorithm"
    COMPARE = "compare"              # "Difference between BFS and DFS"
    EXAMPLE = "example"              # "Give me an example of recursion"
    EXERCISE = "exercise"            # "Practice problems for sorting"


@dataclass
class ProcessedQuery:
    original: str
    intent: QueryIntent
    entities: List[str]
    filters: Dict[str, str]
    expanded_queries: List[str]
    hyde_text: Optional[str]


class QueryProcessorAgent:
    """
    LLM-powered query understanding for optimal retrieval.
    """
    
    QUERY_ANALYSIS_PROMPT = """
Analyze this student query for a course learning platform.

<query>
{query}
</query>

<available_filters>
- course_id: Filter by specific course
- category: "theory" or "lab"
- content_type: "slides", "document", "code"
- week_number: 1-16
- language: Programming language for code
</available_filters>

Analyze and return JSON:

{{
    "intent": "factual|conceptual|code_find|code_explain|compare|example|exercise",
    
    "entities": [
        "Key concepts/terms the query is about",
        "Example: ['binary search', 'sorted array', 'algorithm']"
    ],
    
    "filters": {{
        "Detected filters from query context",
        "Example: {{'category': 'lab'}} if asking about code"
    }},
    
    "search_queries": [
        "2-3 reformulated queries optimized for search",
        "Include: original intent, keywords, synonyms"
    ],
    
    "is_code_query": true/false,
    
    "specificity": "broad|focused|specific"
}}
"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def process(self, query: str, context: dict = None) -> ProcessedQuery:
        """
        Process user query for optimal retrieval.
        """
        
        # Step 1: LLM Analysis
        analysis = await self._analyze_query(query)
        
        # Step 2: Generate expanded queries
        expanded = await self._expand_queries(
            query=query,
            analysis=analysis
        )
        
        # Step 3: Optional HyDE for complex queries
        hyde_text = None
        if analysis['intent'] in ['conceptual', 'code_explain']:
            hyde_text = await self._generate_hyde(query, analysis)
        
        return ProcessedQuery(
            original=query,
            intent=QueryIntent(analysis['intent']),
            entities=analysis['entities'],
            filters=analysis.get('filters', {}),
            expanded_queries=expanded,
            hyde_text=hyde_text
        )
    
    async def _analyze_query(self, query: str) -> dict:
        """Classify and parse query."""
        
        prompt = self.QUERY_ANALYSIS_PROMPT.format(query=query)
        
        response = await self.llm.generate(
            prompt=prompt,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        return json.loads(response)
    
    async def _expand_queries(
        self,
        query: str,
        analysis: dict
    ) -> List[str]:
        """
        Generate query variants for better recall.
        """
        
        queries = [query]  # Always include original
        
        # Add LLM-generated variants
        queries.extend(analysis.get('search_queries', []))
        
        # Add entity-based queries
        for entity in analysis.get('entities', []):
            queries.append(entity)
        
        # For code queries, add programming-specific variants
        if analysis.get('is_code_query'):
            queries.append(f"{query} code")
            queries.append(f"{query} implementation")
            queries.append(f"{query} example")
        
        return list(set(queries))  # Deduplicate
    
    async def _generate_hyde(self, query: str, analysis: dict) -> str:
        """
        Generate Hypothetical Document Embedding (HyDE).
        
        Creates a hypothetical "perfect answer" to embed.
        This can improve retrieval for complex conceptual queries.
        """
        
        prompt = f"""
Write a brief, factual answer to this student question as it might appear
in course materials. Write 2-3 sentences, focusing on accuracy.

Question: {query}

Context: This is for a {analysis['intent']} query about {', '.join(analysis['entities'])}.

Answer:
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=200
        )
        
        return response.strip()
```

---

## 🔀 Hybrid Retrieval System

### Dense + Sparse Combination

```python
import chromadb
from chromadb.utils import embedding_functions
import cohere
from rank_bm25 import BM25Okapi
from typing import List, Tuple
import numpy as np


class HybridRetriever:
    """
    Combines dense (semantic) and sparse (keyword) retrieval.
    
    Dense: Cohere embeddings + ChromaDB
    Sparse: BM25 on metadata and content
    Fusion: Reciprocal Rank Fusion
    """
    
    def __init__(
        self,
        chroma_client: chromadb.Client,
        cohere_client: cohere.Client,
        collection_name: str
    ):
        self.chroma = chroma_client
        self.cohere = cohere_client
        self.collection = chroma_client.get_collection(collection_name)
        
        # Initialize BM25 index (built lazily)
        self._bm25_index = None
        self._bm25_docs = None
    
    async def retrieve(
        self,
        processed_query: ProcessedQuery,
        k: int = 30,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4
    ) -> List[dict]:
        """
        Hybrid retrieval with RRF fusion.
        
        Args:
            processed_query: Output from QueryProcessorAgent
            k: Number of final results
            dense_weight: Weight for semantic results
            sparse_weight: Weight for keyword results
        """
        
        # Determine search text
        search_texts = processed_query.expanded_queries
        
        # Add HyDE if available (improves conceptual queries)
        if processed_query.hyde_text:
            search_texts.append(processed_query.hyde_text)
        
        # Build filters from processed query
        where_filter = self._build_filters(processed_query)
        
        # ═══════════════════════════════════════════════════════════
        # DENSE RETRIEVAL (Semantic)
        # ═══════════════════════════════════════════════════════════
        
        dense_results = await self._dense_search(
            queries=search_texts,
            k=50,
            where_filter=where_filter
        )
        
        # ═══════════════════════════════════════════════════════════
        # SPARSE RETRIEVAL (BM25)
        # ═══════════════════════════════════════════════════════════
        
        sparse_results = await self._sparse_search(
            queries=search_texts,
            k=50,
            where_filter=where_filter
        )
        
        # ═══════════════════════════════════════════════════════════
        # RECIPROCAL RANK FUSION
        # ═══════════════════════════════════════════════════════════
        
        fused_results = self._rrf_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            dense_weight=dense_weight,
            sparse_weight=sparse_weight,
            k=k
        )
        
        return fused_results
    
    async def _dense_search(
        self,
        queries: List[str],
        k: int,
        where_filter: dict = None
    ) -> List[Tuple[str, float]]:
        """
        Semantic search using Cohere embeddings.
        """
        
        all_results = {}
        
        for query in queries:
            # Embed query with Cohere
            embedding = self.cohere.embed(
                texts=[query],
                model="embed-english-v3.0",
                input_type="search_query"
            ).embeddings[0]
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Aggregate results (track best score per doc)
            for i, doc_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i]
                # Convert distance to similarity score
                score = 1 / (1 + distance)
                
                if doc_id not in all_results:
                    all_results[doc_id] = {
                        'score': score,
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i]
                    }
                else:
                    # Keep best score
                    all_results[doc_id]['score'] = max(
                        all_results[doc_id]['score'],
                        score
                    )
        
        # Sort by score
        sorted_results = sorted(
            all_results.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        return sorted_results[:k]
    
    async def _sparse_search(
        self,
        queries: List[str],
        k: int,
        where_filter: dict = None
    ) -> List[Tuple[str, float]]:
        """
        BM25 keyword search on content and metadata.
        """
        
        # Ensure BM25 index exists
        if self._bm25_index is None:
            await self._build_bm25_index()
        
        all_results = {}
        
        for query in queries:
            # Tokenize query
            query_tokens = self._tokenize(query)
            
            # BM25 search
            scores = self._bm25_index.get_scores(query_tokens)
            
            # Get top k
            top_indices = np.argsort(scores)[::-1][:k]
            
            for idx in top_indices:
                if scores[idx] > 0:
                    doc_id = self._bm25_docs[idx]['id']
                    
                    # Apply filters if specified
                    if where_filter:
                        if not self._matches_filter(
                            self._bm25_docs[idx]['metadata'],
                            where_filter
                        ):
                            continue
                    
                    if doc_id not in all_results:
                        all_results[doc_id] = {
                            'score': scores[idx],
                            'document': self._bm25_docs[idx]['content'],
                            'metadata': self._bm25_docs[idx]['metadata']
                        }
                    else:
                        all_results[doc_id]['score'] = max(
                            all_results[doc_id]['score'],
                            scores[idx]
                        )
        
        # Sort and return
        sorted_results = sorted(
            all_results.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        return sorted_results[:k]
    
    def _rrf_fusion(
        self,
        dense_results: List[Tuple[str, dict]],
        sparse_results: List[Tuple[str, dict]],
        dense_weight: float,
        sparse_weight: float,
        k: int,
        rrf_k: int = 60
    ) -> List[dict]:
        """
        Reciprocal Rank Fusion to combine dense and sparse results.
        
        RRF Score = Σ (weight / (rrf_k + rank))
        """
        
        rrf_scores = {}
        doc_data = {}
        
        # Score dense results
        for rank, (doc_id, data) in enumerate(dense_results):
            rrf_score = dense_weight / (rrf_k + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + rrf_score
            doc_data[doc_id] = data
        
        # Score sparse results
        for rank, (doc_id, data) in enumerate(sparse_results):
            rrf_score = sparse_weight / (rrf_k + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = data
        
        # Sort by fused score
        sorted_docs = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]
        
        # Build results with metadata
        results = []
        for doc_id, score in sorted_docs:
            results.append({
                'id': doc_id,
                'score': score,
                'content': doc_data[doc_id]['document'],
                'metadata': doc_data[doc_id]['metadata']
            })
        
        return results
    
    async def _build_bm25_index(self):
        """Build BM25 index from ChromaDB documents."""
        
        # Fetch all documents
        all_docs = self.collection.get(
            include=["documents", "metadatas"]
        )
        
        # Prepare for BM25
        self._bm25_docs = []
        tokenized_corpus = []
        
        for i, (doc_id, doc, meta) in enumerate(zip(
            all_docs['ids'],
            all_docs['documents'],
            all_docs['metadatas']
        )):
            # Create searchable text including metadata
            searchable = self._create_searchable_text(doc, meta)
            tokens = self._tokenize(searchable)
            
            self._bm25_docs.append({
                'id': doc_id,
                'content': doc,
                'metadata': meta
            })
            tokenized_corpus.append(tokens)
        
        # Build BM25 index
        self._bm25_index = BM25Okapi(tokenized_corpus)
    
    def _create_searchable_text(self, doc: str, meta: dict) -> str:
        """
        Create text for BM25 including metadata fields.
        
        This allows keyword search on metadata like topics, keywords,
        function names, etc.
        """
        
        parts = [doc]
        
        # Add searchable metadata fields
        searchable_fields = [
            'topics', 'keywords', 'summary', 'function_name',
            'purpose', 'concepts', 'nl_queries', 'title'
        ]
        
        for field in searchable_fields:
            if field in meta:
                value = meta[field]
                if isinstance(value, list):
                    parts.extend(value)
                else:
                    parts.append(str(value))
        
        return " ".join(parts)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        import re
        # Lowercase and split on non-alphanumeric
        return re.findall(r'\w+', text.lower())
    
    def _build_filters(self, query: ProcessedQuery) -> dict:
        """Build ChromaDB filter from processed query."""
        
        if not query.filters:
            return None
        
        conditions = []
        for key, value in query.filters.items():
            conditions.append({key: {"$eq": value}})
        
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}
```

---

## 🎯 Reranking Strategy

### Cohere Rerank Integration

```python
class RerankerPipeline:
    """
    Cross-encoder reranking for precision optimization.
    
    Uses Cohere Rerank to score query-document pairs
    more accurately than embedding similarity alone.
    """
    
    def __init__(self, cohere_client: cohere.Client):
        self.cohere = cohere_client
    
    async def rerank(
        self,
        query: str,
        documents: List[dict],
        top_k: int = 10,
        relevance_threshold: float = 0.3
    ) -> List[dict]:
        """
        Rerank documents using Cohere cross-encoder.
        
        Args:
            query: Original user query
            documents: Retrieved documents with 'content' and 'metadata'
            top_k: Number of results to return
            relevance_threshold: Minimum relevance score
            
        Returns:
            Reranked documents with relevance scores
        """
        
        if not documents:
            return []
        
        # Prepare documents for Cohere
        doc_texts = []
        for doc in documents:
            # Include metadata in reranking text for better scoring
            text = self._prepare_rerank_text(doc)
            doc_texts.append(text)
        
        # Call Cohere Rerank
        rerank_response = self.cohere.rerank(
            query=query,
            documents=doc_texts,
            top_n=min(top_k, len(documents)),
            model="rerank-english-v3.0",
            return_documents=False  # We already have docs
        )
        
        # Build reranked results
        reranked = []
        for result in rerank_response.results:
            if result.relevance_score >= relevance_threshold:
                doc = documents[result.index]
                reranked.append({
                    **doc,
                    'relevance_score': result.relevance_score,
                    'original_rank': result.index
                })
        
        return reranked
    
    def _prepare_rerank_text(self, doc: dict) -> str:
        """
        Prepare document text for reranking.
        
        Include relevant metadata to help the reranker
        understand context.
        """
        
        parts = []
        meta = doc.get('metadata', {})
        
        # Add title/summary if available
        if title := meta.get('title'):
            parts.append(f"Title: {title}")
        if summary := meta.get('summary'):
            parts.append(f"Summary: {summary}")
        
        # Main content
        parts.append(doc['content'])
        
        return "\n".join(parts)


class AdaptiveReranker(RerankerPipeline):
    """
    Adaptive reranking that adjusts strategy based on query type.
    """
    
    async def rerank_adaptive(
        self,
        processed_query: ProcessedQuery,
        documents: List[dict],
        top_k: int = 10
    ) -> List[dict]:
        """
        Rerank with query-aware adjustments.
        """
        
        # Adjust threshold based on intent
        thresholds = {
            QueryIntent.FACTUAL: 0.4,      # Need high relevance
            QueryIntent.CONCEPTUAL: 0.3,   # Accept broader results
            QueryIntent.CODE_FIND: 0.35,   # Code needs precision
            QueryIntent.CODE_EXPLAIN: 0.3, # Explanation can be broader
            QueryIntent.COMPARE: 0.25,     # Need multiple perspectives
            QueryIntent.EXAMPLE: 0.3,      # Examples can vary
        }
        
        threshold = thresholds.get(
            processed_query.intent,
            0.3
        )
        
        # For code queries, boost code results
        if processed_query.intent in [QueryIntent.CODE_FIND, QueryIntent.CODE_EXPLAIN]:
            documents = self._boost_code_results(documents)
        
        return await self.rerank(
            query=processed_query.original,
            documents=documents,
            top_k=top_k,
            relevance_threshold=threshold
        )
    
    def _boost_code_results(
        self,
        documents: List[dict],
        boost_factor: float = 1.2
    ) -> List[dict]:
        """
        Boost code documents for code-focused queries.
        """
        
        boosted = []
        for doc in documents:
            meta = doc.get('metadata', {})
            if meta.get('chunk_type') == 'code':
                doc = doc.copy()
                doc['score'] = doc.get('score', 1.0) * boost_factor
            boosted.append(doc)
        
        # Re-sort
        return sorted(boosted, key=lambda x: x.get('score', 0), reverse=True)
```

---

## 📦 Context Assembly

### Building LLM-Ready Context

```python
@dataclass
class RetrievedContext:
    """Final context ready for LLM generation."""
    chunks: List[dict]
    total_tokens: int
    citations: List[dict]
    context_string: str


class ContextAssembler:
    """
    Assembles retrieved chunks into optimal LLM context.
    
    Responsibilities:
    1. Deduplicate overlapping content
    2. Order for coherence
    3. Add citation markers
    4. Fit within token budget
    """
    
    def __init__(self, max_tokens: int = 6000):
        self.max_tokens = max_tokens
    
    def assemble(
        self,
        reranked_docs: List[dict],
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
        
        for source_group in grouped:
            for doc in source_group:
                # Check token budget
                doc_tokens = self._count_tokens(doc['content'])
                if total_tokens + doc_tokens > self.max_tokens:
                    break
                
                # Create citation
                citation = self._create_citation(doc)
                citations.append(citation)
                
                # Format chunk with citation marker
                formatted = self._format_chunk(doc, citation)
                context_parts.append(formatted)
                
                total_tokens += doc_tokens
        
        # Build final context string
        context_string = self._build_context_string(
            context_parts,
            query
        )
        
        return RetrievedContext(
            chunks=deduped[:len(context_parts)],
            total_tokens=total_tokens,
            citations=citations,
            context_string=context_string
        )
    
    def _deduplicate(self, docs: List[dict]) -> List[dict]:
        """
        Remove duplicate or highly overlapping chunks.
        
        Uses content similarity to detect duplicates.
        """
        
        seen_content = set()
        deduped = []
        
        for doc in docs:
            # Create content fingerprint
            content = doc['content']
            fingerprint = self._create_fingerprint(content)
            
            if fingerprint not in seen_content:
                seen_content.add(fingerprint)
                deduped.append(doc)
        
        return deduped
    
    def _create_fingerprint(self, content: str) -> str:
        """Create content fingerprint for deduplication."""
        # Normalize and hash first 500 chars
        normalized = " ".join(content.lower().split())[:500]
        return hash(normalized)
    
    def _group_by_source(
        self,
        docs: List[dict]
    ) -> List[List[dict]]:
        """
        Group documents by source file for coherent presentation.
        """
        
        from collections import defaultdict
        
        groups = defaultdict(list)
        
        for doc in docs:
            source = doc.get('metadata', {}).get('source_file', 'unknown')
            groups[source].append(doc)
        
        # Sort groups by average relevance score
        sorted_groups = sorted(
            groups.values(),
            key=lambda g: sum(d.get('relevance_score', 0) for d in g) / len(g),
            reverse=True
        )
        
        return sorted_groups
    
    def _create_citation(self, doc: dict) -> dict:
        """
        Create citation info for a document chunk.
        """
        
        meta = doc.get('metadata', {})
        
        citation = {
            'id': doc.get('id'),
            'source_file': meta.get('source_file', 'Unknown'),
            'document_title': meta.get('document_title', meta.get('source_file', 'Unknown')),
        }
        
        # Add location info
        if slide := meta.get('slide_number'):
            citation['location'] = f"Slide {slide}"
            citation['type'] = 'slide'
        elif page := meta.get('page_number'):
            citation['location'] = f"Page {page}"
            citation['type'] = 'page'
        elif line_start := meta.get('line_start'):
            citation['location'] = f"Lines {line_start}-{meta.get('line_end', line_start)}"
            citation['type'] = 'code'
            citation['function'] = meta.get('function_name')
        
        # Create citation key
        citation['key'] = self._create_citation_key(citation)
        
        return citation
    
    def _create_citation_key(self, citation: dict) -> str:
        """Create short citation key like [1], [2], etc."""
        # Will be assigned sequentially
        return f"[{citation.get('id', '?')[:8]}]"
    
    def _format_chunk(self, doc: dict, citation: dict) -> str:
        """
        Format chunk with citation marker for LLM context.
        """
        
        meta = doc.get('metadata', {})
        
        # Build header
        header_parts = [f"Source: {citation['document_title']}"]
        if loc := citation.get('location'):
            header_parts.append(loc)
        if section := meta.get('section'):
            header_parts.append(f"Section: {section}")
        
        header = " | ".join(header_parts)
        
        return f"""
<context citation="{citation['key']}">
[{header}]

{doc['content']}
</context>
"""
    
    def _build_context_string(
        self,
        parts: List[str],
        query: ProcessedQuery
    ) -> str:
        """
        Build the final context string for LLM.
        """
        
        intro = f"""
The following context is retrieved from course materials to help answer the query.
Each section is marked with a citation key that should be referenced in the answer.

Query: {query.original}
Query Type: {query.intent.value}

Retrieved Context:
"""
        
        return intro + "\n".join(parts)
    
    def _count_tokens(self, text: str) -> int:
        """Approximate token count."""
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
```

---

## 🔧 Complete Retrieval Pipeline

### Putting It All Together

```python
class RetrievalPipeline:
    """
    Complete retrieval pipeline from query to context.
    
    Usage:
        pipeline = RetrievalPipeline(...)
        context = await pipeline.retrieve("How does quicksort work?")
    """
    
    def __init__(
        self,
        llm_client,
        cohere_client,
        chroma_client,
        collection_name: str
    ):
        self.query_processor = QueryProcessorAgent(llm_client)
        self.retriever = HybridRetriever(
            chroma_client=chroma_client,
            cohere_client=cohere_client,
            collection_name=collection_name
        )
        self.reranker = AdaptiveReranker(cohere_client)
        self.assembler = ContextAssembler(max_tokens=6000)
    
    async def retrieve(
        self,
        query: str,
        filters: dict = None,
        top_k: int = 10
    ) -> RetrievedContext:
        """
        Full retrieval pipeline.
        
        Args:
            query: User query string
            filters: Optional filters (course_id, category, etc.)
            top_k: Number of final chunks
            
        Returns:
            RetrievedContext ready for generation
        """
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 1: Query Processing
        # ═══════════════════════════════════════════════════════════
        
        processed = await self.query_processor.process(query)
        
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
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 3: Reranking
        # ═══════════════════════════════════════════════════════════
        
        reranked = await self.reranker.rerank_adaptive(
            processed_query=processed,
            documents=candidates,
            top_k=top_k
        )
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 4: Context Assembly
        # ═══════════════════════════════════════════════════════════
        
        context = self.assembler.assemble(
            reranked_docs=reranked,
            query=processed
        )
        
        return context
```

---

## 📊 Performance Expectations

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL PIPELINE PERFORMANCE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Latency Breakdown (typical query):                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Stage                    │ Time       │ Notes                    │   │
│  ├──────────────────────────┼────────────┼──────────────────────────│   │
│  │ Query Processing         │ 200-400ms  │ LLM call                 │   │
│  │ Dense Retrieval          │ 100-200ms  │ Cohere embed + ChromaDB  │   │
│  │ Sparse Retrieval         │ 50-100ms   │ BM25 local               │   │
│  │ RRF Fusion               │ 10-20ms    │ Local computation        │   │
│  │ Cohere Rerank            │ 300-500ms  │ API call                 │   │
│  │ Context Assembly         │ 20-50ms    │ Local computation        │   │
│  ├──────────────────────────┼────────────┼──────────────────────────│   │
│  │ TOTAL                    │ 700-1300ms │ Well under 2s target     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Quality Metrics (expected):                                            │
│  • Recall@10: > 0.85                                                   │
│  • Precision@10: > 0.70 (with reranking)                               │
│  • MRR: > 0.75                                                         │
│  • Citation Accuracy: 100%                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Related Files

- **[04-CODE-PREPROCESSING.md](./04-CODE-PREPROCESSING.md)** - Code enrichment for better retrieval
- **[06-GENERATION-VALIDATION.md](./06-GENERATION-VALIDATION.md)** - Using retrieved context
- **[07-IMPLEMENTATION-TEMPLATES.md](./07-IMPLEMENTATION-TEMPLATES.md)** - Full code templates

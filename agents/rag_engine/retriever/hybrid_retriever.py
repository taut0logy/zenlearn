"""
Hybrid Retriever - Dense + Sparse search with RRF fusion.

Combines semantic search (Cohere embeddings + ChromaDB) with
keyword search (BM25) for optimal recall.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from services.embedding_service import EmbeddingService, get_embedding_service
from services.vector_store_service import VectorStoreService, get_vector_store
from utils.logger import logger

from .query_processor import ProcessedQuery


@dataclass
class RetrievalResult:
    """A single retrieval result."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str = "dense"  # "dense" or "sparse"


class SimpleBM25:
    """
    Simple BM25 implementation for sparse search.
    
    Avoids external dependency while providing keyword matching.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_freqs = {}
        self.idf = {}
        self.doc_lens = []
        self.avgdl = 0
        self.n_docs = 0
    
    def fit(self, documents: List[Dict[str, Any]]):
        """Build BM25 index from documents."""
        self.corpus = documents
        self.n_docs = len(documents)
        
        # Tokenize and compute document frequencies
        tokenized = []
        df = {}
        
        for doc in documents:
            text = self._get_searchable_text(doc)
            tokens = self._tokenize(text)
            tokenized.append(tokens)
            
            # Count unique terms per doc
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1
        
        self.doc_freqs = df
        self.doc_lens = [len(t) for t in tokenized]
        self.avgdl = sum(self.doc_lens) / max(len(self.doc_lens), 1)
        
        # Compute IDF
        for term, freq in df.items():
            self.idf[term] = self._compute_idf(freq)
        
        self._tokenized = tokenized
    
    def search(self, query: str, k: int = 50) -> List[Tuple[int, float]]:
        """
        Search for query, return (doc_index, score) pairs.
        """
        query_tokens = self._tokenize(query)
        scores = []
        
        for idx, doc_tokens in enumerate(self._tokenized):
            score = self._score_document(query_tokens, doc_tokens, self.doc_lens[idx])
            if score > 0:
                scores.append((idx, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize with unigrams and bigrams for phrase matching."""
        words = re.findall(r'\w+', text.lower())
        # Add bigrams for phrase matching (e.g., "neural_network", "hate_speech")
        bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]
        return words + bigrams
    
    def _get_searchable_text(self, doc: Dict) -> str:
        """Get searchable text including metadata."""
        parts = [doc.get('content', '')]
        meta = doc.get('metadata', {})
        
        # Add searchable metadata fields
        for field in ['title', 'summary', 'keywords', 'topics', 'function_name', 'nl_queries']:
            if field in meta:
                val = meta[field]
                if isinstance(val, list):
                    parts.extend(str(v) for v in val)
                else:
                    parts.append(str(val))
        
        return ' '.join(parts)
    
    def _compute_idf(self, doc_freq: int) -> float:
        """Compute IDF score."""
        import math
        return math.log((self.n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def _score_document(self, query_tokens: List[str], doc_tokens: List[str], doc_len: int) -> float:
        """Compute BM25 score for a document."""
        score = 0.0
        doc_term_freqs = {}
        
        for token in doc_tokens:
            doc_term_freqs[token] = doc_term_freqs.get(token, 0) + 1
        
        for term in query_tokens:
            if term not in doc_term_freqs:
                continue
            
            freq = doc_term_freqs[term]
            idf = self.idf.get(term, 0)
            
            # BM25 formula
            numerator = freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * numerator / denominator
        
        return score


class HybridRetriever:
    """
    Combines dense (semantic) and sparse (keyword) retrieval.
    
    Dense: Cohere embeddings + ChromaDB
    Sparse: BM25 on content and metadata
    Fusion: Reciprocal Rank Fusion
    """
    
    def __init__(
        self,
        collection_name: str = "zenlearn",
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStoreService] = None
    ):
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or get_vector_store(collection_name)
        self.collection_name = collection_name
        
        # BM25 index (built lazily)
        self._bm25 = None
        self._bm25_docs = None
    
    async def retrieve(
        self,
        processed_query: ProcessedQuery,
        k: int = 30,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4
    ) -> List[RetrievalResult]:
        """
        Hybrid retrieval with RRF fusion.
        
        Args:
            processed_query: Output from QueryProcessor
            k: Number of final results
            dense_weight: Weight for semantic results
            sparse_weight: Weight for keyword results
            
        Returns:
            List of RetrievalResult sorted by relevance
        """
        # Get search texts
        search_texts = processed_query.expanded_queries.copy()
        if processed_query.hyde_text:
            search_texts.append(processed_query.hyde_text)
        
        # Build filter from query
        where_filter = self._build_filter(processed_query)
        
        # Dense retrieval
        dense_results = await self._dense_search(
            queries=search_texts,
            k=50,
            where_filter=where_filter
        )
        
        # Sparse retrieval
        sparse_results = await self._sparse_search(
            queries=search_texts,
            k=50,
            where_filter=where_filter
        )
        
        # RRF fusion
        fused = self._rrf_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            dense_weight=dense_weight,
            sparse_weight=sparse_weight,
            k=k
        )
        
        return fused
    
    async def _dense_search(
        self,
        queries: List[str],
        k: int,
        where_filter: Optional[Dict] = None
    ) -> List[RetrievalResult]:
        """Semantic search using Cohere embeddings."""
        all_results = {}
        
        for query in queries[:5]:  # Limit queries to avoid too many API calls
            try:
                # First try with filter
                results = self.vector_store.search(
                    query=query,
                    k=k,
                    where=where_filter
                )
                
                for r in results:
                    doc_id = r['id']
                    score = 1 / (1 + r.get('distance', 0))
                    
                    if doc_id not in all_results or score > all_results[doc_id].score:
                        all_results[doc_id] = RetrievalResult(
                            id=doc_id,
                            content=r['content'],
                            metadata=r.get('metadata', {}),
                            score=score,
                            source="dense"
                        )
            except Exception as e:
                # Retry without filter if filter caused the error
                if where_filter and "where" in str(e).lower():
                    logger.warning(f"Dense search filter failed, retrying without filter")
                    try:
                        results = self.vector_store.search(
                            query=query,
                            k=k,
                            where=None
                        )
                        for r in results:
                            doc_id = r['id']
                            score = 1 / (1 + r.get('distance', 0))
                            if doc_id not in all_results or score > all_results[doc_id].score:
                                all_results[doc_id] = RetrievalResult(
                                    id=doc_id,
                                    content=r['content'],
                                    metadata=r.get('metadata', {}),
                                    score=score,
                                    source="dense"
                                )
                    except Exception as retry_err:
                        logger.warning(f"Dense search retry failed: {retry_err}")
                else:
                    logger.warning(f"Dense search failed: {e}")
        
        # Sort by score
        results = list(all_results.values())
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]
    
    async def _sparse_search(
        self,
        queries: List[str],
        k: int,
        where_filter: Optional[Dict] = None
    ) -> List[RetrievalResult]:
        """BM25 keyword search."""
        # Build BM25 index if needed
        if self._bm25 is None:
            await self._build_bm25_index()
        
        if not self._bm25_docs:
            return []
        
        all_results = {}
        
        for query in queries[:5]:
            bm25_results = self._bm25.search(query, k=k)
            
            for idx, score in bm25_results:
                doc = self._bm25_docs[idx]
                doc_id = doc['id']
                
                # Apply filter if specified
                if where_filter and not self._matches_filter(doc.get('metadata', {}), where_filter):
                    continue
                
                if doc_id not in all_results or score > all_results[doc_id].score:
                    all_results[doc_id] = RetrievalResult(
                        id=doc_id,
                        content=doc['content'],
                        metadata=doc.get('metadata', {}),
                        score=score,
                        source="sparse"
                    )
        
        results = list(all_results.values())
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]
    
    async def _build_bm25_index(self):
        """Build BM25 index from vector store documents."""
        try:
            # Get all documents from ChromaDB
            all_docs = self.vector_store.get_all()
            
            if not all_docs:
                logger.warning("No documents found for BM25 index")
                self._bm25_docs = []
                self._bm25 = SimpleBM25()
                return
            
            self._bm25_docs = all_docs
            self._bm25 = SimpleBM25()
            self._bm25.fit(all_docs)
            
            logger.info(f"Built BM25 index with {len(all_docs)} documents")
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            self._bm25_docs = []
            self._bm25 = SimpleBM25()
    
    def _rrf_fusion(
        self,
        dense_results: List[RetrievalResult],
        sparse_results: List[RetrievalResult],
        dense_weight: float,
        sparse_weight: float,
        k: int,
        rrf_k: int = 60
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion to combine results.
        
        RRF Score = Σ (weight / (rrf_k + rank))
        """
        rrf_scores = {}
        result_data = {}
        
        # Score dense results
        for rank, result in enumerate(dense_results):
            rrf_score = dense_weight / (rrf_k + rank + 1)
            rrf_scores[result.id] = rrf_scores.get(result.id, 0) + rrf_score
            result_data[result.id] = result
        
        # Score sparse results
        for rank, result in enumerate(sparse_results):
            rrf_score = sparse_weight / (rrf_k + rank + 1)
            rrf_scores[result.id] = rrf_scores.get(result.id, 0) + rrf_score
            if result.id not in result_data:
                result_data[result.id] = result
        
        # Sort by fused score
        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build final results
        fused = []
        for doc_id, score in sorted_ids[:k]:
            result = result_data[doc_id]
            fused.append(RetrievalResult(
                id=result.id,
                content=result.content,
                metadata=result.metadata,
                score=score,
                source="hybrid"
            ))
        
        return fused
    
    def _build_filter(self, query: ProcessedQuery) -> Optional[Dict]:
        """Build ChromaDB filter from processed query."""
        if not query.filters:
            return None
        
        # Valid ChromaDB metadata keys (must exist in stored documents)
        valid_keys = {'course_id', 'category', 'content_type', 'week_number', 'language', 'file_type', 'chunk_type'}
        
        conditions = []
        for key, value in query.filters.items():
            # Skip invalid keys or empty values
            if key not in valid_keys:
                logger.debug(f"Skipping invalid filter key: {key}")
                continue
            if value is None or value == "":
                continue
            # ChromaDB requires string, int, float, or bool for filter values
            if not isinstance(value, (str, int, float, bool)):
                continue
            conditions.append({key: {"$eq": value}})
        
        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}
    
    def _matches_filter(self, metadata: Dict, where_filter: Dict) -> bool:
        """Check if metadata matches filter."""
        if not where_filter:
            return True
        
        for key, condition in where_filter.items():
            if key == "$and":
                return all(self._matches_filter(metadata, c) for c in condition)
            elif key == "$or":
                return any(self._matches_filter(metadata, c) for c in condition)
            elif isinstance(condition, dict):
                if "$eq" in condition:
                    if metadata.get(key) != condition["$eq"]:
                        return False
            else:
                if metadata.get(key) != condition:
                    return False
        
        return True
    
    def invalidate_bm25_cache(self):
        """Invalidate BM25 index to rebuild on next search."""
        self._bm25 = None
        self._bm25_docs = None


# Factory
def get_hybrid_retriever(
    collection_name: str = "zenlearn",
    embedding_service: Optional[EmbeddingService] = None
) -> HybridRetriever:
    """Create a hybrid retriever instance."""
    return HybridRetriever(collection_name, embedding_service)

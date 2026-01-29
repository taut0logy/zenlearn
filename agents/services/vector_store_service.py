"""
Vector Store Service using ChromaDB.

Provides document storage, retrieval, and semantic search capabilities.
"""

import hashlib
from typing import List, Dict, Any, Optional
from config.chromadb import get_chroma_client
from config.settings import settings
from services.embedding_service import embedding_service
from utils.logger import logger


class VectorStoreService:
    """Service for vector storage and retrieval using ChromaDB."""
    
    def __init__(self, collection_name: str = "rag-documents"):
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.embedding_service = embedding_service
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of text content
            metadatas: List of metadata dicts
            ids: Optional document IDs (auto-generated if not provided)
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Generate IDs if not provided
        if ids is None:
            ids = [self._generate_id(doc) for doc in documents]
        
        # Generate embeddings
        embeddings = self.embedding_service.embed_documents(documents)
        
        # Sanitize metadata for ChromaDB
        clean_metadatas = [self._sanitize_metadata(m) for m in metadatas]
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=clean_metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(documents)} documents to vector store")
        return ids
    
    def search(
        self,
        query: str,
        k: int = 10,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results
            where: Optional metadata filters
            
        Returns:
            List of results with id, content, metadata, score
        """
        query_embedding = self.embedding_service.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'score': 1 / (1 + results['distances'][0][i])
            })
        
        return formatted
    
    def delete(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents")
    
    def get_by_filter(
        self,
        where: Dict,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get documents matching a metadata filter."""
        results = self.collection.get(
            where=where,
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        formatted = []
        for i in range(len(results['ids'])):
            formatted.append({
                'id': results['ids'][i],
                'content': results['documents'][i],
                'metadata': results['metadatas'][i]
            })
        
        return formatted
    
    def get_all(self, limit: int = 300) -> List[Dict[str, Any]]:
        """
        Get all documents from the collection.
        
        Used for building BM25 index.
        Note: ChromaDB Cloud has a quota limit of 300 per request.
        """
        try:
            results = self.collection.get(
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            formatted = []
            for i in range(len(results['ids'])):
                formatted.append({
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
            
            return formatted
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []
    
    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()

    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID from content hash."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """
        Sanitize metadata for ChromaDB.
        ChromaDB only accepts str, int, float, bool values.
        """
        clean = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                clean[key] = value
            elif isinstance(value, list):
                if all(isinstance(v, str) for v in value):
                    clean[key] = ",".join(value)
                else:
                    clean[key] = str(value)
            elif value is None:
                clean[key] = ""
            else:
                clean[key] = str(value)
        return clean


# Factory function for creating instances
def get_vector_store(collection_name: str = "rag-documents") -> VectorStoreService:
    """Get a vector store instance for a specific collection."""
    return VectorStoreService(collection_name)

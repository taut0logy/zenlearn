"""
Cohere Embedding Service for RAG Engine.

Provides document and query embedding using Cohere's embed-v4.0 model.
"""

import cohere
from typing import List
from config.settings import settings
from utils.logger import logger


class EmbeddingService:
    """Service for generating embeddings using Cohere API."""
    
    def __init__(self, model: str = "embed-v4.0"):
        self.client = cohere.Client(settings.COHERE_API_KEY)
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed documents for storage/indexing.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            response = self.client.embed(
                texts=texts,
                model=self.model,
                input_type="search_document",
                embedding_types=["float"]
            )
            return response.embeddings.float
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            raise
    
    def embed_query(self, query: str) -> List[float]:
        """
        Embed a query for searching.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embed(
                texts=[query],
                model=self.model,
                input_type="search_query",
                embedding_types=["float"]
            )
            return response.embeddings.float[0]
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise
    
    def embed_batch(
        self, 
        texts: List[str], 
        batch_size: int = 96
    ) -> List[List[float]]:
        """
        Embed large number of texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call
            
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.embed_documents(batch)
            all_embeddings.extend(embeddings)
            logger.info(f"Embedded batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        
        return all_embeddings


# Singleton instance
embedding_service = EmbeddingService()


def get_embedding_service(model: str = "embed-v4.0") -> EmbeddingService:
    """Get or create an embedding service instance."""
    return EmbeddingService(model)


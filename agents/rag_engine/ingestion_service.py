"""
Ingestion Service - Process and store files.

Handles file processing, chunking, and storage in ChromaDB.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from rag_engine.chunker import ChunkingService, Chunk, get_chunking_service
from services.vector_store_service import VectorStoreService, get_vector_store
from utils.logger import logger


class IngestionService:
    """
    Service for ingesting files into the RAG system.
    
    Handles:
    - File type detection
    - Content chunking
    - Embedding generation
    - Vector storage
    """
    
    def __init__(
        self,
        collection_name: str = "zenlearn",
        chunking_service: Optional[ChunkingService] = None,
        vector_store: Optional[VectorStoreService] = None
    ):
        self.chunking_service = chunking_service or get_chunking_service()
        self.vector_store = vector_store or get_vector_store(collection_name)
        self.collection_name = collection_name
    
    def ingest_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Ingest a single file.
        
        Args:
            file_path: Path to the file
            metadata: Optional base metadata
            
        Returns:
            List of chunk IDs stored
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Ingesting file: {file_path.name}")
        
        # Build metadata
        base_metadata = metadata or {}
        base_metadata.update({
            'source_file': str(file_path),
            'filename': file_path.name,
            'file_type': file_path.suffix.lower(),
        })
        
        # Chunk the file
        chunks = self.chunking_service.chunk_file(str(file_path), base_metadata)
        
        if not chunks:
            logger.warning(f"No chunks generated from {file_path.name}")
            return []
        
        logger.info(f"Generated {len(chunks)} chunks from {file_path.name}")
        
        # Store chunks
        return self._store_chunks(chunks)
    
    def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """
        Ingest all supported files from a directory.
        
        Args:
            directory_path: Path to directory
            recursive: If True, process subdirectories
            metadata: Optional base metadata for all files
            
        Returns:
            Dict mapping filenames to their chunk IDs
        """
        directory = Path(directory_path)
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")
        
        supported_exts = set()
        for exts in self.chunking_service.get_supported_extensions().values():
            supported_exts.update(exts)
        
        results = {}
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                try:
                    file_metadata = (metadata or {}).copy()
                    chunk_ids = self.ingest_file(str(file_path), file_metadata)
                    results[file_path.name] = chunk_ids
                except Exception as e:
                    logger.error(f"Failed to ingest {file_path.name}: {e}")
                    results[file_path.name] = []
        
        total_chunks = sum(len(ids) for ids in results.values())
        logger.info(f"Ingested {len(results)} files with {total_chunks} total chunks")
        
        return results
    
    def ingest_content(
        self,
        content: str,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Ingest raw content (not from file).
        
        Args:
            content: Raw text content
            content_type: Type of content ('code', 'text', 'pdf')
            metadata: Optional metadata
            
        Returns:
            List of chunk IDs stored
        """
        base_metadata = metadata or {}
        chunks = self.chunking_service.chunk_content(content, content_type, base_metadata)
        
        if not chunks:
            return []
        
        return self._store_chunks(chunks)
    
    def _store_chunks(self, chunks: List[Chunk]) -> List[str]:
        """Store chunks in vector store."""
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        ids = self.vector_store.add_documents(
            documents=documents,
            metadatas=metadatas
        )
        
        return ids
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Get all IDs and delete
            all_docs = self.vector_store.get_all(limit=300)
            if all_docs:
                ids = [doc['id'] for doc in all_docs]
                self.vector_store.delete(ids)
                logger.info(f"Cleared {len(ids)} documents from collection")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        count = self.vector_store.count()
        return {
            'collection_name': self.collection_name,
            'document_count': count,
        }


# Factory
def get_ingestion_service(
    collection_name: str = "zenlearn"
) -> IngestionService:
    """Create an ingestion service instance."""
    return IngestionService(collection_name)

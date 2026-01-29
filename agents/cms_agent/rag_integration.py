"""
RAG Integration Service - Connects CMS operations with RAG engine.

Handles:
- File ingestion on upload (background)
- Chunk cleanup on delete
- Metadata updates on edit
"""

from typing import Dict, Any, Optional
from pathlib import Path

from rag_engine.ingestion_service import get_ingestion_service
from services.vector_store_service import get_vector_store
from utils.logger import logger


class RAGIntegrationService:
    """
    Bridge between CMS and RAG engine.

    Provides synchronous methods that can be called from FastAPI BackgroundTasks.
    """

    def __init__(self, collection_name: str = "zenlearn"):
        self.collection_name = collection_name
        self._ingestion_service = None
        self._vector_store = None

    @property
    def ingestion_service(self):
        """Lazy initialization of ingestion service."""
        if self._ingestion_service is None:
            self._ingestion_service = get_ingestion_service(self.collection_name)
        return self._ingestion_service

    @property
    def vector_store(self):
        """Lazy initialization of vector store."""
        if self._vector_store is None:
            self._vector_store = get_vector_store(self.collection_name)
        return self._vector_store

    def ingest_material(
        self,
        file_path: str,
        material_id: str,
        course_id: str,
        course_no: str,
        material_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Ingest a material file into the RAG system.

        Called as a background task after file upload.

        Args:
            file_path: Absolute path to the file
            material_id: UUID of the CourseMaterial record
            course_id: UUID of the Course
            course_no: Course number (e.g., "CSE422")
            material_type: "theory" or "lab"
            metadata: Optional additional metadata

        Returns:
            Number of chunks created
        """
        logger.info(f"[INGESTION] ===== Starting ingestion =====")
        logger.info(f"[INGESTION] File: {file_path}")
        logger.info(f"[INGESTION] Material ID: {material_id}")
        logger.info(f"[INGESTION] Course: {course_no} ({course_id})")
        logger.info(f"[INGESTION] Type: {material_type}")
        logger.debug(f"[INGESTION] Extra metadata: {metadata}")

        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"[INGESTION] File not found: {file_path}")
                return 0

            logger.debug(f"[INGESTION] File exists, size: {path.stat().st_size} bytes")
            logger.debug(f"[INGESTION] File extension: {path.suffix}")

            # Build metadata for chunks
            chunk_metadata = {
                "material_id": str(material_id),
                "course_id": str(course_id),
                "course_no": course_no,
                "material_type": material_type,
                **(metadata or {}),
            }
            logger.debug(f"[INGESTION] Chunk metadata: {chunk_metadata}")

            logger.info(f"[INGESTION] Calling ingestion service...")
            chunk_ids = self.ingestion_service.ingest_file(str(path), chunk_metadata)

            logger.info(f"[INGESTION] ✅ SUCCESS: Created {len(chunk_ids)} chunks")
            if chunk_ids:
                logger.debug(f"[INGESTION] First chunk ID: {chunk_ids[0]}")
            logger.info(f"[INGESTION] ===== Ingestion complete =====")
            return len(chunk_ids)

        except Exception as e:
            logger.error(f"[INGESTION] ❌ FAILED: {e}", exc_info=True)
            return 0

    def delete_material_chunks(self, file_path: str) -> int:
        """
        Delete all chunks associated with a material file.

        Args:
            file_path: Path to the file (used as source_file in metadata)

        Returns:
            Number of chunks deleted
        """
        try:
            # Find chunks by source_file metadata
            chunks = self.vector_store.get_by_filter(
                where={"source_file": file_path}, limit=500
            )

            if not chunks:
                logger.info(f"No chunks found for: {file_path}")
                return 0

            chunk_ids = [chunk["id"] for chunk in chunks]
            self.vector_store.delete(chunk_ids)

            logger.info(f"Deleted {len(chunk_ids)} chunks for: {file_path}")
            return len(chunk_ids)

        except Exception as e:
            logger.error(f"Failed to delete chunks for {file_path}: {e}")
            return 0

    def delete_material_chunks_by_id(self, material_id: str) -> int:
        """
        Delete all chunks by material_id metadata.

        Alternative when file path is not available.
        """
        try:
            chunks = self.vector_store.get_by_filter(
                where={"material_id": material_id}, limit=500
            )

            if not chunks:
                return 0

            chunk_ids = [chunk["id"] for chunk in chunks]
            self.vector_store.delete(chunk_ids)

            logger.info(f"Deleted {len(chunk_ids)} chunks for material: {material_id}")
            return len(chunk_ids)

        except Exception as e:
            logger.error(f"Failed to delete chunks for material {material_id}: {e}")
            return 0


# Singleton instance
_rag_integration: Optional[RAGIntegrationService] = None


def get_rag_integration(collection_name: str = "zenlearn") -> RAGIntegrationService:
    """Get RAG integration service instance."""
    global _rag_integration
    if _rag_integration is None:
        _rag_integration = RAGIntegrationService(collection_name)
    return _rag_integration

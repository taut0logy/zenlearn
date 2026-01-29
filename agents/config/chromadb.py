import os
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from fastapi import Depends
from config.settings import settings
from utils.logger import logger

_client: ClientAPI | None = None
_collection: Collection | None = None


def get_chroma_client(use_cloud: bool = False) -> ClientAPI:
    """
    Get ChromaDB client.
    
    Args:
        use_cloud: If True, use cloud client. If False, use local.
                   If None, auto-detect based on settings.
    """
    global _client
    
    if _client is not None:
        return _client
    
    # Auto-detect: use cloud if API key is set, otherwise use local
    if use_cloud is None:
        use_cloud = bool(settings.CHROMA_API_KEY and settings.CHROMA_API_KEY != "")
    
    if use_cloud:
        try:
            logger.info("Connecting to ChromaDB Cloud...")
            _client = chromadb.CloudClient(
                api_key=settings.CHROMA_API_KEY,
                tenant=settings.CHROMA_TENANT,
                database=settings.CHROMA_DATABASE,
            )
            # Test connection
            _client.heartbeat()
            logger.info("ChromaDB Cloud connected")
        except Exception as e:
            logger.warning(f"ChromaDB Cloud connection failed: {e}")
            logger.info("Falling back to local ChromaDB...")
            use_cloud = False
    
    if not use_cloud:
        # Use local persistent storage
        persist_dir = os.path.join(settings.BASE_DIR, "data", "chromadb")
        os.makedirs(persist_dir, exist_ok=True)
        _client = chromadb.PersistentClient(path=persist_dir)
        logger.info(f"Using local ChromaDB at {persist_dir}")
    
    return _client


def reset_chroma_client():
    """Reset the ChromaDB client (useful for switching between cloud/local)."""
    global _client, _collection
    _client = None
    _collection = None


def get_chroma_collection(
    client: ClientAPI = Depends(get_chroma_client), 
    collection: str = "bcf-26"
) -> Collection:
    global _collection
    if _collection is None:
        _collection = client.get_or_create_collection(
            name=collection,
        )
    return _collection

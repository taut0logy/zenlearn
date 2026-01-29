import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from fastapi import Depends
from config.settings import settings

_client: ClientAPI | None = None
_collection: Collection | None = None

def get_chroma_client() -> ClientAPI:
	global _client
	if _client is None:
		_client = chromadb.CloudClient(
            api_key=settings.CHROMA_API_KEY,
            tenant=settings.CHROMA_TENANT,
            database=settings.CHROMA_DATABASE,
        )
	return _client

def get_chroma_collection(client: ClientAPI = Depends(get_chroma_client), collection: str = "bcf-26") -> Collection:
	global _collection
	if _collection is None:
		_collection = client.get_or_create_collection(
		    name=collection,
		)
	return _collection

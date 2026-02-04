"""
ChromaDB-based Memory for conversation context.

Stores and retrieves conversation memories using ChromaDB with Cohere embeddings.
Automatically extracts and stores important information from conversations.
"""

import cohere
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from config.settings import settings
from config.chromadb import get_chroma_client
from utils.logger import logger


class ChatMemory:
    """
    ChromaDB-based memory system for chat conversations.
    
    Features:
    - Automatic memory extraction from conversations
    - Semantic memory retrieval
    - Per-chat and cross-chat memory storage
    """
    
    COLLECTION_NAME = "chat_memories"
    
    def __init__(self):
        self.client = get_chroma_client()
        self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
        self._collection = None
    
    @property
    def collection(self):
        """Get or create the memories collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Extracted conversation memories"}
            )
        return self._collection
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Cohere."""
        response = self.cohere_client.embed(
            texts=[text],
            model="embed-english-v3.0",
            input_type="search_document"
        )
        return response.embeddings[0]
    
    def _get_query_embedding(self, text: str) -> List[float]:
        """Get query embedding for text using Cohere."""
        response = self.cohere_client.embed(
            texts=[text],
            model="embed-english-v3.0",
            input_type="search_query"
        )
        return response.embeddings[0]
    
    def add_memory(
        self,
        user_id: str,
        chat_id: str,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a memory entry.
        
        Args:
            user_id: User ID
            chat_id: Chat session ID
            content: Memory content
            memory_type: Type of memory (conversation, fact, preference, etc.)
            metadata: Additional metadata
            
        Returns:
            Memory ID
        """
        try:
            memory_id = str(uuid4())
            embedding = self._get_embedding(content)
            
            doc_metadata = {
                "user_id": str(user_id),
                "chat_id": str(chat_id),
                "memory_type": memory_type,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[doc_metadata]
            )
            
            logger.debug(f"Added memory {memory_id} for user {user_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise
    
    def add_memories_batch(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add multiple memories at once.
        
        Args:
            memories: List of memory dicts with user_id, chat_id, content, memory_type
            
        Returns:
            List of memory IDs
        """
        if not memories:
            return []
            
        try:
            contents = [m["content"] for m in memories]
            
            # Get embeddings in batch
            response = self.cohere_client.embed(
                texts=contents,
                model="embed-english-v3.0",
                input_type="search_document"
            )
            embeddings = response.embeddings
            
            ids = [str(uuid4()) for _ in memories]
            metadatas = [
                {
                    "user_id": str(m["user_id"]),
                    "chat_id": str(m["chat_id"]),
                    "memory_type": m.get("memory_type", "conversation"),
                    "created_at": datetime.utcnow().isoformat(),
                }
                for m in memories
            ]
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(memories)} memories in batch")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to batch add memories: {e}")
            raise
    
    def get_memories(
        self,
        user_id: str,
        query: str,
        chat_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for a query.
        
        Args:
            user_id: User ID to filter memories
            query: Query to search for relevant memories
            chat_id: Optional chat ID to filter to specific chat
            memory_type: Optional memory type filter
            n_results: Number of results to return
            
        Returns:
            List of relevant memories with metadata
        """
        try:
            query_embedding = self._get_query_embedding(query)
            
            # Build filter
            where_filter = {"user_id": str(user_id)}
            if chat_id:
                where_filter["chat_id"] = str(chat_id)
            if memory_type:
                where_filter["memory_type"] = memory_type
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                where=where_filter,
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted.append({
                        "id": results["ids"][0][i] if results["ids"] else None,
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "relevance": 1 - results["distances"][0][i] if results["distances"] else None
                    })
            
            logger.debug(f"Retrieved {len(formatted)} memories for query")
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to get memories: {e}")
            return []
    
    def get_chat_memories(
        self,
        chat_id: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a specific chat.
        
        Args:
            chat_id: Chat session ID
            n_results: Maximum number of results
            
        Returns:
            List of memories for the chat
        """
        try:
            results = self.collection.get(
                where={"chat_id": str(chat_id)},
                limit=n_results,
                include=["documents", "metadatas"]
            )
            
            formatted = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    formatted.append({
                        "id": results["ids"][i] if results["ids"] else None,
                        "content": doc,
                        "metadata": results["metadatas"][i] if results["metadatas"] else {}
                    })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to get chat memories: {e}")
            return []
    
    def clear_chat_memories(self, chat_id: str) -> int:
        """
        Clear all memories for a chat.
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            Number of memories deleted
        """
        try:
            results = self.collection.get(
                where={"chat_id": str(chat_id)},
                include=[]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Cleared {len(results['ids'])} memories for chat {chat_id}")
                return len(results["ids"])
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return 0
    
    def clear_user_memories(self, user_id: str) -> int:
        """
        Clear all memories for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of memories deleted
        """
        try:
            results = self.collection.get(
                where={"user_id": str(user_id)},
                include=[]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Cleared {len(results['ids'])} memories for user {user_id}")
                return len(results["ids"])
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear user memories: {e}")
            return 0
    
    def format_memories_for_context(
        self,
        memories: List[Dict[str, Any]],
        max_length: int = 2000
    ) -> str:
        """
        Format memories for inclusion in the agent context.
        
        Args:
            memories: List of memory dicts
            max_length: Maximum total length
            
        Returns:
            Formatted string for context
        """
        if not memories:
            return ""
        
        formatted_parts = ["**Relevant memories:**"]
        current_length = len(formatted_parts[0])
        
        for memory in memories:
            content = memory["content"]
            memory_type = memory.get("metadata", {}).get("memory_type", "memory")
            
            entry = f"- [{memory_type}]: {content}"
            
            if current_length + len(entry) > max_length:
                break
                
            formatted_parts.append(entry)
            current_length += len(entry)
        
        return "\n".join(formatted_parts)


# Singleton instance
_chat_memory: Optional[ChatMemory] = None


def get_chat_memory() -> ChatMemory:
    """Get the chat memory instance."""
    global _chat_memory
    if _chat_memory is None:
        _chat_memory = ChatMemory()
    return _chat_memory

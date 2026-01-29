"""
Semantic Search Tool for chat history.

Uses ChromaDB to enable semantic search over past conversations,
allowing the agent to recall relevant context from previous chats.
"""

import cohere
from typing import List, Dict, Any, Optional
from uuid import UUID
from langchain_core.tools import tool
from config.settings import settings
from config.chromadb import get_chroma_client
from utils.logger import logger


class SemanticSearchTool:
    """
    Semantic search over chat history using ChromaDB.
    
    Enables the agent to recall and reference past conversations.
    """
    
    COLLECTION_NAME = "chat_history"
    
    def __init__(self):
        self.client = get_chroma_client()
        self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
        self._collection = None
    
    @property
    def collection(self):
        """Get or create the chat history collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Chat message history for semantic search"}
            )
        return self._collection
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Cohere."""
        response = self.cohere_client.embed(
            texts=[text],
            model="embed-english-v3.0",
            input_type="search_query"
        )
        return response.embeddings[0]
    
    def _get_embeddings_batch(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """Get embeddings for multiple texts."""
        if not texts:
            return []
        response = self.cohere_client.embed(
            texts=texts,
            model="embed-english-v3.0",
            input_type=input_type
        )
        return response.embeddings
    
    def index_message(
        self, 
        message_id: str,
        chat_id: str, 
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Index a message for semantic search.
        
        Args:
            message_id: Unique message ID
            chat_id: Chat session ID
            user_id: User ID who owns the chat
            role: Message role (user/assistant)
            content: Message content
            metadata: Additional metadata
        """
        try:
            embedding = self._get_embedding(content)
            
            doc_metadata = {
                "chat_id": str(chat_id),
                "user_id": str(user_id),
                "role": role,
                **(metadata or {})
            }
            
            self.collection.add(
                ids=[str(message_id)],
                embeddings=[embedding],
                documents=[content],
                metadatas=[doc_metadata]
            )
            
            logger.debug(f"Indexed message {message_id} for chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Failed to index message: {e}")
    
    def index_messages_batch(
        self,
        messages: List[Dict[str, Any]]
    ) -> None:
        """
        Index multiple messages at once.
        
        Args:
            messages: List of message dicts with id, chat_id, user_id, role, content
        """
        if not messages:
            return
            
        try:
            contents = [m["content"] for m in messages]
            embeddings = self._get_embeddings_batch(contents)
            
            ids = [str(m["id"]) for m in messages]
            metadatas = [
                {
                    "chat_id": str(m["chat_id"]),
                    "user_id": str(m["user_id"]),
                    "role": m["role"]
                }
                for m in messages
            ]
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"Indexed {len(messages)} messages")
            
        except Exception as e:
            logger.error(f"Failed to batch index messages: {e}")
    
    def search(
        self, 
        query: str, 
        user_id: str,
        chat_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search chat history semantically.
        
        Args:
            query: Search query
            user_id: Filter to user's chats only
            chat_id: Optional filter to specific chat
            n_results: Number of results to return
            
        Returns:
            List of matching messages with metadata
        """
        try:
            query_embedding = self._get_embedding(query)
            
            # Build filter
            where_filter = {"user_id": str(user_id)}
            if chat_id:
                where_filter["chat_id"] = str(chat_id)
            
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
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None,
                        "id": results["ids"][0][i] if results["ids"] else None
                    })
            
            logger.info(f"Semantic search for '{query[:50]}...' returned {len(formatted)} results")
            return formatted
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def delete_chat_messages(self, chat_id: str) -> None:
        """
        Delete all indexed messages for a chat.
        
        Args:
            chat_id: Chat ID to delete messages for
        """
        try:
            # Get all message IDs for this chat
            results = self.collection.get(
                where={"chat_id": str(chat_id)},
                include=[]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} indexed messages for chat {chat_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete chat messages from index: {e}")
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results for the agent.
        
        Args:
            results: Search results from search()
            
        Returns:
            Formatted string for LLM context
        """
        if not results:
            return "No relevant messages found in chat history."
        
        formatted_parts = ["**Relevant messages from chat history:**\n"]
        
        for i, result in enumerate(results, 1):
            role = result["metadata"].get("role", "unknown")
            content = result["content"]
            
            formatted_parts.append(
                f"{i}. [{role.upper()}]: {content[:500]}{'...' if len(content) > 500 else ''}"
            )
        
        return "\n".join(formatted_parts)


# Singleton instance
_semantic_search_tool = SemanticSearchTool()


@tool
def search_chat_history(query: str, user_id: str) -> str:
    """
    Search through past chat conversations for relevant information.
    
    Use this tool when you need to recall or reference information
    from previous conversations with the user.
    
    Args:
        query: What to search for in chat history
        user_id: The user's ID to search their chats
        
    Returns:
        Relevant messages from past conversations
    """
    results = _semantic_search_tool.search(query, user_id)
    return _semantic_search_tool.format_search_results(results)


# Export for service use
def get_semantic_search_tool() -> SemanticSearchTool:
    """Get the semantic search tool instance."""
    return _semantic_search_tool

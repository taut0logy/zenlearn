"""
Mem0-based Memory for conversation context.

Uses Mem0 with:
- Vector Store: ChromaDB
- Embeddings: Cohere (via LangChain)
- LLM: Gemini 2.5 Flash
- Reranking: Built-in LLM Reranker with Academic Prompt
"""

import os
from typing import List, Dict, Any, Optional
from mem0 import Memory
from langchain_cohere import CohereEmbeddings
from config.settings import settings
from utils.logger import logger


class ChatMemory:
    """
    Mem0-based memory system for chat conversations.
    Wraps the Mem0 client with project-specific configuration.
    """

    def __init__(self):
        # ensure directories exist
        os.makedirs("data/chroma", exist_ok=True)

        # Set environment variables required by Mem0/LangChain
        os.environ["COHERE_API_KEY"] = settings.COHERE_API_KEY
        os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY

        # Initialize LangChain Embeddings
        cohere_embeddings = CohereEmbeddings(
            model="embed-english-v3.0", cohere_api_key=settings.COHERE_API_KEY
        )

        # Custom Reranking Prompt for Academic Context
        academic_rerank_prompt = """
        You are an intelligent assistant for a university learning platform. 
        Rate how relevant this memory is for answering the student's current query.

        Prioritize:
        1. **Course Specifics**: Facts about usage of specific tools, libraries, or methodologies mentioned in this course.
        2. **User Learning State**: Notes on what the student already knows, is confused by, or has successfully mastered.
        3. **Preferences**: Preferred coding languages (e.g., Python vs C++), explanation styles (visual vs theoretical).
        4. **Recency**: If two memories conflict, favor the one that implies a more recent state of mind.

        Query: {query}
        Memory: {memory}
        Score:
        """

        # Mem0 Configuration
        config = {
            "vector_store": {
                "provider": "chromadb",
                "config": {
                    "collection_name": "mem0_chat_memories",
                    "path": "data/chroma",
                },
            },
            "llm": {
                "provider": "gemini",
                "config": {
                    "model": "gemini-2.5-flash",
                    "api_key": settings.GEMINI_API_KEY,
                    "temperature": 0.2,
                },
            },
            "embedder": {
                "provider": "langchain",
                "config": {"model": cohere_embeddings},
            },
            "reranker": {
                "provider": "llm_reranker",
                "config": {
                    "llm": {
                        "provider": "gemini",
                        "config": {
                            "model": "gemini-2.5-flash",
                            "api_key": settings.GEMINI_API_KEY,
                        },
                    },
                    "top_k": 5,
                    "custom_prompt": academic_rerank_prompt,
                },
            },
        }

        try:
            self.memory = Memory.from_config(config)
            logger.info("Mem0 initialized successfully with Gemini/Cohere/Chroma.")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            raise

    def add_memory(
        self,
        user_id: str,
        chat_id: str,
        content: str,  # Mem0 expects messages list for .add(), or text. We will adapt.
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a memory entry via Mem0.

        Note: Mem0 is intelligent and extracts facts. 'content' should ideally be the full interaction,
        but we will pass what we have.
        """
        try:
            # Prepare metadata
            meta = {
                "chat_id": str(chat_id),
                "memory_type": memory_type,
                **(metadata or {}),
            }

            # Mem0 .add() typically takes a list of messages or a string text.
            # Passing the raw content string allows Mem0 to extract facts from it.
            # If content is a conversation turn, it's better to format as messages,
            # but usually this method is called with a specific string to remember.
            result = self.memory.add(content, user_id=str(user_id), metadata=meta)

            # Mem0 add returns a list of added memory items (facts)
            if result and isinstance(result, list):
                logger.debug(f"Mem0 extracted {len(result)} facts for user {user_id}")
                return result[0].get("id", "unknown") if result else "unknown"

            return "unknown"  # Mem0 doesn't always return a single ID

        except Exception as e:
            logger.error(f"Failed to add memory via Mem0: {e}")
            # Non-blocking failure for memory
            return ""

    def add_memories_batch(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Add multiple memories (Not optimal in Mem0, wrapping sequential adds)."""
        ids = []
        for m in memories:
            res = self.add_memory(
                user_id=m["user_id"],
                chat_id=m["chat_id"],
                content=m["content"],
                memory_type=m.get("memory_type", "conversation"),
            )
            ids.append(res)
        return ids

    def get_memories(
        self,
        user_id: str,
        query: str,
        chat_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for a query using Mem0 search + rerank.
        """
        try:
            # Construct Mem0 filters if supported (Mem0 metadata filtering is limited in basic search)
            # Basic search: self.memory.search(query, user_id=...)
            filters = {}
            if chat_id:
                filters["chat_id"] = str(chat_id)

            # Search with Reranking enabled (configured in __init__)
            results = self.memory.search(
                query=query,
                user_id=str(user_id),
                limit=n_results,
                metadata=filters if filters else None,
            )

            # Format results to match expected interface
            # Mem0 results: [{'memory': '...', 'score': 0.9, 'metadata': {...}, 'id': ...}]
            formatted = []
            for res in results:
                formatted.append(
                    {
                        "id": res.get("id"),
                        "content": res.get("memory"),
                        "metadata": res.get("metadata", {}),
                        "relevance": res.get("score"),  # Populated by reranker
                    }
                )

            logger.debug(f"Mem0 retrieved {len(formatted)} memories")
            return formatted

        except Exception as e:
            logger.error(f"Failed to get memories via Mem0: {e}")
            return []

    def get_chat_memories(
        self, chat_id: str, user_id: str, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a specific chat.
        Requires user_id to fetch and filter from Mem0.
        """
        try:
            # Fetch all memories for the user
            all_memories = self.memory.get_all(user_id=str(user_id))

            # Filter by chat_id in metadata
            chat_memories = []
            if all_memories:
                for mem in all_memories:
                    metadata = mem.get("metadata", {})
                    # Mem0 v1 returns dicts. Ensure metadata is a dict.
                    if metadata and str(metadata.get("chat_id")) == str(chat_id):
                        chat_memories.append(
                            {
                                "id": mem.get("id"),
                                "content": mem.get("memory"),
                                "metadata": metadata,
                                "created_at": mem.get("created_at"),
                            }
                        )

            # Mem0 usually returns recent first or standard order.
            return chat_memories[:n_results]

        except Exception as e:
            logger.error(f"Failed to get chat memories: {e}")
            return []

    def clear_chat_memories(self, chat_id: str, user_id: str) -> int:
        """
        Clear all memories for a chat.
        Requires user_id to find and delete specific memories.
        """
        try:
            # 1. Get all memories for the user
            all_memories = self.memory.get_all(user_id=str(user_id))

            # 2. Identify memories belonging to this chat
            to_delete = []
            if all_memories:
                for mem in all_memories:
                    if str(mem.get("metadata", {}).get("chat_id")) == str(chat_id):
                        to_delete.append(mem.get("id"))

            # 3. Delete them one by one
            deleted_count = 0
            for mem_id in to_delete:
                if mem_id:
                    self.memory.delete(mem_id)
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleared {deleted_count} memories for chat {chat_id}")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return 0

    def clear_user_memories(self, user_id: str) -> int:
        """Clear all memories for a user."""
        try:
            self.memory.delete_all(user_id=str(user_id))
            return 1
        except Exception:
            return 0

    def format_memories_for_context(
        self, memories: List[Dict[str, Any]], max_length: int = 2000
    ) -> str:
        """
        Format memories for inclusion in the agent context.
        """
        if not memories:
            return ""

        formatted_parts = ["**Relevant Key Facts & Memories:**"]
        current_length = len(formatted_parts[0])

        for memory in memories:
            content = memory["content"]
            # Mem0 memories are usually concise facts.

            entry = f"- {content}"

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

"""
Chat context management.

Handles building and managing the conversation context window
for the chat agent, including system prompts, message history,
and context truncation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .schemas import MessageRole, AgentMessage
from .memory import get_chat_memory
from utils.logger import logger


# Token estimation (rough approximation: 1 token ≈ 4 chars for English)
def estimate_tokens(text: str) -> int:
    """Estimate token count for text."""
    return len(text) // 4


class ChatContext:
    """
    Manages conversation context for the chat agent.
    
    Responsibilities:
    - Build context from message history
    - Include relevant memories
    - Truncate to fit context window
    - Generate system prompts
    """
    
    # Maximum context window (conservative for Gemini)
    MAX_CONTEXT_TOKENS = 30000
    
    # Reserved tokens for response
    RESPONSE_RESERVE = 4000
    
    # System prompt
    SYSTEM_PROMPT = """You are ZenLearn, an AI-powered learning assistant for university courses.

Your capabilities:
1. **Answer Questions**: Provide clear, educational explanations on course topics
2. **Search Wikipedia**: Use the wikipedia_search tool for factual information
3. **Recall Conversations**: Reference past discussions when relevant
4. **Explain Concepts**: Break down complex topics into understandable parts

Guidelines:
- Be educational and supportive in your responses
- Cite sources when using external information
- Ask clarifying questions when needed
- Provide examples to illustrate concepts
- Admit when you don't know something

You have access to the following tools:
- **wikipedia_search**: Search Wikipedia for factual information about any topic
- **search_chat_history**: Search past conversations for relevant context

Always be helpful, accurate, and supportive of the student's learning journey."""

    def __init__(self, user_id: str, chat_id: str):
        self.user_id = user_id
        self.chat_id = chat_id
        self.memory = get_chat_memory()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return self.SYSTEM_PROMPT
    
    def build_context(
        self,
        messages: List[Dict[str, Any]],
        current_query: Optional[str] = None,
        include_memories: bool = True
    ) -> List[AgentMessage]:
        """
        Build the context for the agent from message history.
        
        Args:
            messages: List of message dicts from database
            current_query: Current user query (for memory retrieval)
            include_memories: Whether to include relevant memories
            
        Returns:
            List of AgentMessage objects for the agent
        """
        context_messages = []
        
        # Add system prompt
        context_messages.append(AgentMessage(
            role=MessageRole.SYSTEM,
            content=self.get_system_prompt()
        ))
        
        # Get relevant memories if enabled
        if include_memories and current_query:
            memories = self._get_relevant_memories(current_query)
            if memories:
                memory_content = self.memory.format_memories_for_context(memories)
                context_messages.append(AgentMessage(
                    role=MessageRole.SYSTEM,
                    content=f"Context from previous conversations:\n{memory_content}"
                ))
        
        # Calculate available tokens
        system_tokens = sum(estimate_tokens(m.content) for m in context_messages)
        available_tokens = self.MAX_CONTEXT_TOKENS - self.RESPONSE_RESERVE - system_tokens
        
        # Process message history (most recent first for truncation)
        history_messages = []
        current_tokens = 0
        
        for msg in reversed(messages):
            msg_content = msg.get("content", "")
            msg_tokens = estimate_tokens(msg_content)
            
            if current_tokens + msg_tokens > available_tokens:
                # Truncate this message to fit
                remaining_tokens = available_tokens - current_tokens
                if remaining_tokens > 100:  # Only include if meaningful
                    truncated_chars = remaining_tokens * 4
                    msg_content = msg_content[:truncated_chars] + "..."
                    history_messages.insert(0, AgentMessage(
                        role=MessageRole(msg["role"]),
                        content=msg_content
                    ))
                break
            
            history_messages.insert(0, AgentMessage(
                role=MessageRole(msg["role"]),
                content=msg_content
            ))
            current_tokens += msg_tokens
        
        context_messages.extend(history_messages)
        
        logger.debug(
            f"Built context with {len(context_messages)} messages, "
            f"~{system_tokens + current_tokens} tokens"
        )
        
        return context_messages
    
    def _get_relevant_memories(
        self,
        query: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get relevant memories for the current query.
        
        Args:
            query: Current user query
            n_results: Number of memories to retrieve
            
        Returns:
            List of relevant memories
        """
        try:
            # Get memories from current chat and cross-chat
            memories = self.memory.get_memories(
                user_id=self.user_id,
                query=query,
                n_results=n_results
            )
            
            # Filter by relevance threshold
            relevant = [m for m in memories if m.get("relevance", 0) > 0.5]
            
            return relevant
            
        except Exception as e:
            logger.error(f"Failed to get memories: {e}")
            return []
    
    def extract_and_store_memories(
        self,
        user_message: str,
        assistant_response: str
    ) -> None:
        """
        Extract and store important memories from the conversation turn.
        
        This is a simple extraction - could be enhanced with LLM-based extraction.
        
        Args:
            user_message: The user's message
            assistant_response: The assistant's response
        """
        try:
            # Store user's question/topic as a memory
            if len(user_message) > 20:  # Only meaningful messages
                self.memory.add_memory(
                    user_id=self.user_id,
                    chat_id=self.chat_id,
                    content=f"User asked: {user_message[:500]}",
                    memory_type="question"
                )
            
            # Store key parts of the response
            if len(assistant_response) > 100:
                # Take first paragraph or first 500 chars as memory
                first_para = assistant_response.split("\n\n")[0][:500]
                self.memory.add_memory(
                    user_id=self.user_id,
                    chat_id=self.chat_id,
                    content=f"Discussed: {first_para}",
                    memory_type="discussion"
                )
                
        except Exception as e:
            logger.error(f"Failed to extract memories: {e}")
    
    def format_messages_for_llm(
        self,
        messages: List[AgentMessage]
    ) -> List[Dict[str, str]]:
        """
        Format messages for LLM API call.
        
        Args:
            messages: List of AgentMessage objects
            
        Returns:
            List of message dicts in LLM format
        """
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

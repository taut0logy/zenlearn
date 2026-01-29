"""
Chat context management.

Handles building and managing the conversation context window
for the chat agent, including system prompts, message history,
and context truncation.
"""

from typing import List, Dict, Any, Optional
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
1. **Answer Questions**: Provide clear, educational explanations grounded in course materials
2. **Search Course Materials**: Use course_materials_search FIRST for any academic questions
3. **External Knowledge**: Use Wikipedia/web search only when course materials don't have the answer
4. **Recall Conversations**: Reference past discussions when relevant
5. **Explain Concepts**: Break down complex topics with citations

## CRITICAL: Search Priority Chain

You MUST follow this priority when answering questions:

1. **FIRST: Course Materials** - ALWAYS search course materials first using `course_materials_search`
2. **SECOND: Wikipedia** - For encyclopedic knowledge not in course materials
3. **THIRD: Web Search** - For current events or additional context
4. **LAST: Generic Response** - Only if no sources are available

## MANDATORY: Citations and Source References

When using information from course materials, you MUST:

1. **Include inline citations** using this exact format: `[Source: filename, location]`
   - Example: "Binary search has O(log n) complexity [Source: Lecture 3.pptx, Slide 12]"
   - Example: "The algorithm uses divide and conquer [Source: Chapter5.pdf, Page 45]"

2. **Add a References section** at the end of your response when citing sources:
   ```
   ---
   **📚 Sources Used:**
   - [Lecture 3.pptx, Slide 12]
   - [Chapter5.pdf, Page 45]
   ```

3. **Never fabricate citations** - only cite sources actually returned by the search tool

## Tools Available:

- **course_materials_search**: Search uploaded course content (slides, PDFs, code) - USE THIS FIRST
- **wikipedia_search**: Search Wikipedia for factual, encyclopedic information
- **duckduckgo_search**: Search the web for current info, definitions, and quick facts

## Response Formatting:

Use rich markdown formatting to make your responses clear and visually appealing:

### Code Blocks
Use fenced code blocks with language identifiers for syntax highlighting:
```python
def example():
    return "Hello, World!"
```

### Mermaid Diagrams
Use mermaid for flowcharts and diagrams. Follow this syntax EXACTLY:

**Graph Direction:**
- `graph TD` = top to down
- `graph LR` = left to right

**Node Shapes:**
- `A[Rectangle]` - process/step
- `A{Diamond}` - decision/condition  
- `A(Rounded)` - start/end
- `A((Circle))` - connector

**Connections:**
- `A --> B` - arrow
- `A --> |label| B` - arrow with text
- `A --- B` - line without arrow
- `A -.-> B` - dotted arrow
- `A ==> B` - thick arrow

**CRITICAL RULES (must follow):**
1. Use ONLY letters, numbers, spaces in node text
2. NO parentheses () inside square brackets []
3. NO special symbols: < > { } [ ] inside labels
4. Keep labels short and descriptive

**Example - Algorithm Flow:**
```mermaid
graph TD
    A[Start] --> B{Check condition}
    B --> |Yes| C[Process data]
    B --> |No| D[Skip step]
    C --> E[Calculate result]
    D --> E
    E --> F((End))
```

### Callouts
Use callouts for important information:
:::note
This is a note with helpful information.
:::

:::warning
This is a warning about potential issues.
:::

:::tip
This is a helpful tip or suggestion.
:::

### Text Formatting
- Use **bold** for emphasis
- Use *italic* for terms and definitions
- Use `inline code` for code references
- Use ~~strikethrough~~ for corrections

### Tables
Use tables for structured information:
| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |

### Lists
- Use bullet points for unordered lists
1. Use numbers for ordered/step-by-step instructions

## CONTENT GENERATION COMMANDS:
If the user asks to "generate content", "create a guide", "make a lab", or uses slash commands like:
- `/content [topic]` -> Generate theory/guide
- `/lab [topic]` -> Generate coding lab relative to the topic
- `/image [description]` -> Generate explanatory image
- `/pdf [topic]` -> Generate PDF (same as content)

**REQUIRED WORKFLOW for Content Generation:**
1. **SEARCH FIRST**: Use `course_materials_search` to find relevant information about the topic.
2. **GENERATE SECOND**: Call `generate_learning_content` with the topic AND the search results as `context`.
   - `content_type`: "theory" or "lab" based on request
   - `context`: Pass the *full content* of the search results to ensure the generated content is grounded in the course.

Always be helpful, accurate, and supportive of the student's learning journey.
Remember: ALWAYS search course materials FIRST before using external sources."""

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
        include_memories: bool = True,
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
        context_messages.append(
            AgentMessage(role=MessageRole.SYSTEM, content=self.get_system_prompt())
        )

        # Get relevant memories if enabled
        if include_memories and current_query:
            memories = self._get_relevant_memories(current_query)
            if memories:
                memory_content = self.memory.format_memories_for_context(memories)
                context_messages.append(
                    AgentMessage(
                        role=MessageRole.SYSTEM,
                        content=f"Context from previous conversations:\n{memory_content}",
                    )
                )

        # Calculate available tokens
        system_tokens = sum(estimate_tokens(m.content) for m in context_messages)
        available_tokens = (
            self.MAX_CONTEXT_TOKENS - self.RESPONSE_RESERVE - system_tokens
        )

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
                    history_messages.insert(
                        0,
                        AgentMessage(
                            role=MessageRole(msg["role"]), content=msg_content
                        ),
                    )
                break

            history_messages.insert(
                0, AgentMessage(role=MessageRole(msg["role"]), content=msg_content)
            )
            current_tokens += msg_tokens

        context_messages.extend(history_messages)

        logger.debug(
            f"Built context with {len(context_messages)} messages, "
            f"~{system_tokens + current_tokens} tokens"
        )

        return context_messages

    def _get_relevant_memories(
        self, query: str, n_results: int = 3
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
                user_id=self.user_id, query=query, n_results=n_results
            )

            # Filter by relevance threshold
            relevant = [m for m in memories if m.get("relevance", 0) > 0.5]

            return relevant

        except Exception as e:
            logger.error(f"Failed to get memories: {e}")
            return []

    def extract_and_store_memories(
        self, user_message: str, assistant_response: str
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
                    memory_type="question",
                )

            # Store key parts of the response
            if len(assistant_response) > 100:
                # Take first paragraph or first 500 chars as memory
                first_para = assistant_response.split("\n\n")[0][:500]
                self.memory.add_memory(
                    user_id=self.user_id,
                    chat_id=self.chat_id,
                    content=f"Discussed: {first_para}",
                    memory_type="discussion",
                )

        except Exception as e:
            logger.error(f"Failed to extract memories: {e}")

    def format_messages_for_llm(
        self, messages: List[AgentMessage]
    ) -> List[Dict[str, str]]:
        """
        Format messages for LLM API call.

        Args:
            messages: List of AgentMessage objects

        Returns:
            List of message dicts in LLM format
        """
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

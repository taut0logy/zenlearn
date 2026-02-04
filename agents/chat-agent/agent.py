"""
LangGraph-based Chat Agent.

Implements a conversational agent with tool use capabilities
using LangGraph for structured agent workflows.
"""

from typing import TypedDict, Annotated, Sequence, Optional, AsyncGenerator
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from config.settings import settings
from utils.logger import logger
from .tools.course_materials_search import course_materials_search_tool
from .tools.wikipedia_mcp import wikipedia_tool
from .tools.duckduckgo_search import duckduckgo_search_tool
from .tools.content_gen import content_gen_tool
from .tools.validated_code_gen import generate_validated_code
from google.api_core import exceptions as google_exceptions


class AgentState(TypedDict):
    """State for the chat agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: str
    chat_id: str


class ChatAgent:
    """
    LangGraph-based conversational agent with tool use.

    Features:
    - Course materials RAG search (PRIMARY)
    - Wikipedia search for external knowledge
    - Web search for current information
    - Streaming response generation
    - Tool call handling
    """

    def __init__(self):
        # Initialize LLM with function calling
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
            convert_system_message_to_human=True,
        )

        # Initialize tools
        self.tools = [
            course_materials_search_tool,  # PRIMARY: Search course content first
            content_gen_tool,  # SPECIALIZED: Generate learning content/labs
            generate_validated_code,  # SPECIALIZED: Generate & Validate Python Code
            wikipedia_tool,  # SECONDARY: Encyclopedia knowledge
            duckduckgo_search_tool,  # TERTIARY: Web search fallback
        ]

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph agent graph."""

        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self.tools))

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges
        workflow.add_conditional_edges(
            "agent", self._should_continue, {"continue": "tools", "end": END}
        )

        # Tools always go back to agent
        workflow.add_edge("tools", "agent")

        # Compile
        return workflow.compile()

    async def _agent_node(self, state: AgentState) -> dict:
        """Agent node that decides what to do next."""
        messages = state["messages"]

        try:
            response = await self.llm_with_tools.ainvoke(messages)

            # Debug: Print Gemini response
            print("\n" + "=" * 50)
            print("GEMINI LLM RESPONSE:")
            print("=" * 50)
            print(
                f"Content: {response.content[:1000] if response.content else 'No content'}"
            )
            if hasattr(response, "tool_calls") and response.tool_calls:
                print(f"Tool Calls: {response.tool_calls}")
            print(f"{'=' * 50}\n")

            return {"messages": [response]}
        except Exception as e:
            logger.error(f"Agent node error: {e}")
            error_message = AIMessage(
                content=f"I apologize, but I encountered an error: {str(e)}"
            )
            return {"messages": [error_message]}

    def _should_continue(self, state: AgentState) -> str:
        """Determine if we should continue with tools or end."""
        messages = state["messages"]
        last_message = messages[-1]

        # If the LLM made tool calls, continue to tool node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        # Otherwise end
        return "end"

    async def invoke(
        self, user_id: str, chat_id: str, messages: list[dict], system_prompt: str
    ) -> str:
        """
        Invoke the agent with a conversation.

        Args:
            user_id: User ID
            chat_id: Chat ID
            messages: Conversation messages
            system_prompt: System prompt

        Returns:
            Agent response text
        """
        # Convert to LangChain messages
        lc_messages = [SystemMessage(content=system_prompt)]

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        # Create initial state
        initial_state = AgentState(
            messages=lc_messages, user_id=user_id, chat_id=chat_id
        )

        try:
            # Run the graph
            result = await self.graph.ainvoke(initial_state)

            # Extract the final response
            final_messages = result.get("messages", [])
            if final_messages:
                last_message = final_messages[-1]
                if hasattr(last_message, "content"):
                    return last_message.content

            return "I apologize, but I couldn't generate a response."

        except Exception as e:
            logger.error(f"Agent invocation error: {e}")
            raise

    async def stream(
        self, user_id: str, chat_id: str, messages: list[dict], system_prompt: str
    ) -> AsyncGenerator[dict, None]:
        """
        Stream the agent response.

        Args:
            user_id: User ID
            chat_id: Chat ID
            messages: Conversation messages
            system_prompt: System prompt

        Yields:
            Stream events with type and data
        """
        # Convert to LangChain messages
        lc_messages = [SystemMessage(content=system_prompt)]

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        # Create initial state
        initial_state = AgentState(
            messages=lc_messages, user_id=user_id, chat_id=chat_id
        )

        yield {"event": "start", "data": ""}

        try:
            # Stream through the graph
            async for event in self.graph.astream_events(initial_state, version="v2"):
                event_type = event.get("event", "")

                # Handle different event types
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", None)
                    if chunk and hasattr(chunk, "content"):
                        print(
                            f"DEBUG GEMINI CHUNK: {chunk.content}"
                        )  # Debug: Print raw content
                        content = chunk.content
                        # Handle content as string or list (Gemini 2.5 returns list of parts)
                        if isinstance(content, list):
                            # Extract text from parts
                            text_parts = []
                            for part in content:
                                if isinstance(part, str):
                                    text_parts.append(part)
                                elif hasattr(part, "text"):
                                    text_parts.append(part.text)
                                elif isinstance(part, dict) and "text" in part:
                                    text_parts.append(part["text"])
                            content = "".join(text_parts)

                        if content:
                            yield {"event": "token", "data": content}

                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    yield {"event": "tool_call", "data": f"Using {tool_name}..."}

                elif event_type == "on_tool_end":
                    yield {"event": "tool_result", "data": "Tool completed"}

                elif event_type == "on_custom_event":
                    # Handle custom events (like thinking process updates)
                    event_name = event.get("name", "")
                    if event_name == "progress_update":
                        data = event.get("data", {})
                        message = data.get("message", "")
                        if message:
                            yield {"event": "thinking", "data": message}

            yield {"event": "end", "data": ""}

        except google_exceptions.ResourceExhausted as e:
            logger.error(f"Quota exceeded: {e}")
            yield {
                "event": "error",
                "data": "QUOTA_EXCEEDED: Your AI model quota has been reached. Please try again later.",
            }
        except google_exceptions.GoogleAPICallError as e:
            logger.error(f"Google API error: {e}")
            yield {"event": "error", "data": f"API_ERROR: {str(e)}"}
        except Exception as e:
            logger.error(f"Agent streaming error: {e}")
            yield {"event": "error", "data": str(e)}


# Singleton instance
_chat_agent: Optional[ChatAgent] = None


def get_chat_agent() -> ChatAgent:
    """Get the chat agent instance."""
    global _chat_agent
    if _chat_agent is None:
        _chat_agent = ChatAgent()
    return _chat_agent

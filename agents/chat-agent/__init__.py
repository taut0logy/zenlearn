# Chat Agent Module
"""
ZenLearn Conversational Chat Agent
- ChromaDB-based memory
- Wikipedia MCP integration
- LangGraph agent with streaming
"""

from .service import ChatService
from .router import router

__all__ = ["ChatService", "router"]

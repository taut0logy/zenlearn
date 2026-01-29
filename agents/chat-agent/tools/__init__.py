# Chat Agent Tools
"""
Tool implementations for the chat agent:
- Course Materials RAG search (PRIMARY)
- Wikipedia MCP search
- DuckDuckGo web search
- Semantic search for chat history
"""

from .wikipedia_mcp import WikipediaTool, wikipedia_tool
from .duckduckgo_search import duckduckgo_search_tool
from .semantic_search import SemanticSearchTool
from .course_materials_search import (
    course_materials_search_tool,
    CourseMaterialsSearchTool,
    get_course_materials_tool,
)
from .content_gen import content_gen_tool

__all__ = [
    "WikipediaTool",
    "wikipedia_tool",
    "duckduckgo_search_tool",
    "SemanticSearchTool",
    "course_materials_search_tool",
    "CourseMaterialsSearchTool",
    "get_course_materials_tool",
    "content_gen_tool",
]

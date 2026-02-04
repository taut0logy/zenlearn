"""
DuckDuckGo Search Tool using the duckduckgo-search library.

Provides proper web search capability for the chat agent.
"""

from typing import Optional, List
from langchain_core.tools import tool
from pydantic import BaseModel
from utils.logger import logger


class DuckDuckGoResult(BaseModel):
    """DuckDuckGo search result."""

    title: str
    url: str
    description: str


class DuckDuckGoTool:
    """
    DuckDuckGo web search tool using the duckduckgo-search library.

    Provides real web search results, not just instant answers.
    """

    def __init__(self):
        from duckduckgo_search import DDGS

        self.ddgs = DDGS()

    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        """
        Search DuckDuckGo for the given query.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search result dictionaries
        """
        try:
            logger.info(f"Sending DuckDuckGo search request for: {query}")

            # Use text search for web results
            results = list(self.ddgs.text(query, max_results=max_results))

            # Debug: Print results
            print(f"\n{'=' * 50}")
            print(f"DUCKDUCKGO SEARCH RESULTS ({len(results)} found):")
            print(f"{'=' * 50}")
            for i, r in enumerate(results[:3]):
                print(f"{i + 1}. {r.get('title', 'No title')}")
                print(f"   URL: {r.get('href', 'No URL')}")
                print(f"   {r.get('body', 'No description')[:200]}...")
            print(f"{'=' * 50}\n")

            logger.info(f"DuckDuckGo found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {type(e).__name__}: {e}")
            return []

    async def search_and_format(self, query: str) -> str:
        """
        Search DuckDuckGo and return formatted results.

        Args:
            query: Search query

        Returns:
            Formatted string with search results
        """
        results = await self.search(query)

        if not results:
            return f"No web results found for '{query}'. Try rephrasing your query."

        formatted_results = []
        formatted_results.append(f"**Web Search Results for: {query}**\n")

        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("href", "")
            body = result.get("body", "No description")

            formatted_results.append(f"### {i}. {title}")
            formatted_results.append(f"{body}")
            if url:
                formatted_results.append(f"🔗 [Read more]({url})\n")

        return "\n".join(formatted_results)


# Lazy singleton instance
_duckduckgo_tool: Optional[DuckDuckGoTool] = None


def _get_duckduckgo_tool() -> DuckDuckGoTool:
    """Get or create the DuckDuckGo tool instance."""
    global _duckduckgo_tool
    if _duckduckgo_tool is None:
        _duckduckgo_tool = DuckDuckGoTool()
    return _duckduckgo_tool


@tool
async def duckduckgo_search(query: str) -> str:
    """
    Search the web using DuckDuckGo for current information.

    Use this tool when you need:
    - Current events and news
    - Information not in course materials
    - Real-time data and updates
    - General web search results

    Args:
        query: The search query to look up

    Returns:
        Formatted search results with descriptions and links
    """
    tool_instance = _get_duckduckgo_tool()
    return await tool_instance.search_and_format(query)


# Export for direct use
duckduckgo_search_tool = duckduckgo_search

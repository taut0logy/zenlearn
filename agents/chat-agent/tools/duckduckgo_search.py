"""
DuckDuckGo Search Tool using their free Instant Answer API.

Provides web search capability for the chat agent without requiring an API key.
"""

import httpx
from typing import Optional, List
from langchain_core.tools import tool
from pydantic import BaseModel
from utils.logger import logger
import json


class DuckDuckGoResult(BaseModel):
    """DuckDuckGo search result."""
    title: str
    url: str
    description: str


class DuckDuckGoTool:
    """
    DuckDuckGo Instant Answer API tool.
    
    Free to use, no API key required.
    Returns instant answers, related topics, and web results.
    """
    
    BASE_URL = "https://api.duckduckgo.com/"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search(self, query: str) -> dict:
        """
        Search DuckDuckGo for the given query.
        
        Args:
            query: Search query string
            
        Returns:
            Raw API response as dictionary
        """
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        
        try:
            logger.info(f"Sending DuckDuckGo search request for: {query}")
            response = await self.client.get(self.BASE_URL, params=params)
            
            # Debug: Print full response
            print(f"\n{'='*50}")
            print(f"DUCKDUCKGO FULL RESPONSE:")
            print(f"{'='*50}")
            data = response.json()
            print(json.dumps(data, indent=2, default=str)[:3000])
            print(f"{'='*50}\n")
            
            logger.info(f"DuckDuckGo response status: {response.status_code}")
            response.raise_for_status()
            
            return data
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {type(e).__name__}: {e}")
            return {}
    
    async def search_and_format(self, query: str) -> str:
        """
        Search DuckDuckGo and return formatted results.
        
        Args:
            query: Search query
            
        Returns:
            Formatted string with search results
        """
        data = await self.search(query)
        
        if not data:
            return f"No results found for '{query}'."
        
        results = []
        
        # Add abstract (main answer) if available
        abstract = data.get("Abstract")
        abstract_url = data.get("AbstractURL")
        abstract_source = data.get("AbstractSource")
        
        if abstract:
            results.append(f"**{abstract_source}**\n{abstract}\n📎 [Read more]({abstract_url})")
        
        # Add related topics
        related_topics = data.get("RelatedTopics", [])
        for topic in related_topics[:5]:  # Limit to 5
            if isinstance(topic, dict) and "Text" in topic:
                text = topic.get("Text", "")
                url = topic.get("FirstURL", "")
                if text and url:
                    results.append(f"- [{text[:100]}...]({url})" if len(text) > 100 else f"- [{text}]({url})")
        
        # Add definition if available
        definition = data.get("Definition")
        if definition:
            results.append(f"\n**Definition:** {definition}")
        
        if not results:
            # Fallback: try to use Answer field
            answer = data.get("Answer")
            if answer:
                return f"**Answer:** {answer}"
            return f"No detailed results found for '{query}'. Try rephrasing your query."
        
        return "\n\n".join(results)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


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
    - Quick facts and definitions
    - Current information about any topic
    - Multiple perspectives on a subject
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

"""
Wikipedia MCP (Model Context Protocol) Tool for external knowledge retrieval.

This tool wraps Wikipedia API access following MCP patterns for
integration with the LangGraph agent.
"""

import httpx
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from utils.logger import logger


class WikipediaSearchResult(BaseModel):
    """Wikipedia search result."""
    title: str
    snippet: str
    pageid: int


class WikipediaPage(BaseModel):
    """Wikipedia page content."""
    title: str
    pageid: int
    extract: str
    url: str


class WikipediaTool:
    """
    Wikipedia MCP-style tool for external knowledge retrieval.
    
    Uses the Wikipedia API directly for reliable access.
    """
    
    BASE_URL = "https://en.wikipedia.org/w/api.php"
    
    def __init__(self):
        # Wikipedia requires a descriptive User-Agent header
        headers = {
            "User-Agent": "ZenLearnBot/1.0 (https://zenlearn.example.com; contact@zenlearn.example.com)"
        }
        self.client = httpx.AsyncClient(timeout=30.0, headers=headers)
    
    async def search(
        self, 
        query: str, 
        num_results: int = 5
    ) -> List[WikipediaSearchResult]:
        """
        Search Wikipedia for articles matching the query.
        
        Args:
            query: Search query string
            num_results: Maximum number of results to return
            
        Returns:
            List of search results with titles and snippets
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": num_results,
            "format": "json",
            "utf8": 1,
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("query", {}).get("search", []):
                # Clean HTML from snippet
                snippet = item.get("snippet", "")
                snippet = snippet.replace("<span class=\"searchmatch\">", "")
                snippet = snippet.replace("</span>", "")
                
                results.append(WikipediaSearchResult(
                    title=item["title"],
                    snippet=snippet,
                    pageid=item["pageid"]
                ))
            
            logger.info(f"Wikipedia search for '{query}' returned {len(results)} results")
            print(f"DEBUG WIKIPEDIA SEARCH RESULTS: {results}") # Debug: Print search results
            return results
            
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []
    
    async def get_page_summary(
        self, 
        title: str, 
        sentences: int = 5
    ) -> Optional[WikipediaPage]:
        """
        Get a summary of a Wikipedia page.
        
        Args:
            title: Page title
            sentences: Number of sentences to extract
            
        Returns:
            Page content with extract
        """
        params = {
            "action": "query",
            "prop": "extracts|info",
            "exintro": True,
            "explaintext": True,
            "exsentences": sentences,
            "titles": title,
            "inprop": "url",
            "format": "json",
            "utf8": 1,
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            for pageid, page_data in pages.items():
                if pageid == "-1":  # Page not found
                    return None
                    
                return WikipediaPage(
                    title=page_data.get("title", title),
                    pageid=int(pageid),
                    extract=page_data.get("extract", ""),
                    url=page_data.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Wikipedia page fetch error: {e}")
            return None
    
    async def get_page_content(
        self, 
        title: str, 
        max_chars: int = 4000
    ) -> Optional[WikipediaPage]:
        """
        Get full content of a Wikipedia page (truncated).
        
        Args:
            title: Page title
            max_chars: Maximum characters to return
            
        Returns:
            Page content with full extract
        """
        params = {
            "action": "query",
            "prop": "extracts|info",
            "explaintext": True,
            "exchars": max_chars,
            "titles": title,
            "inprop": "url",
            "format": "json",
            "utf8": 1,
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            for pageid, page_data in pages.items():
                if pageid == "-1":
                    return None
                    
                return WikipediaPage(
                    title=page_data.get("title", title),
                    pageid=int(pageid),
                    extract=page_data.get("extract", ""),
                    url=page_data.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Wikipedia content fetch error: {e}")
            return None
    
    async def search_and_summarize(
        self, 
        query: str, 
        num_results: int = 3
    ) -> str:
        """
        Search Wikipedia and return summarized results.
        
        This is the main entry point for the agent tool.
        
        Args:
            query: Search query
            num_results: Number of articles to summarize
            
        Returns:
            Formatted string with search results and summaries
        """
        results = await self.search(query, num_results)
        
        if not results:
            return f"No Wikipedia articles found for '{query}'"
        
        summaries = []
        for result in results:
            page = await self.get_page_summary(result.title, sentences=3)
            if page:
                summaries.append(
                    f"**{page.title}**\n"
                    f"{page.extract}\n"
                    f"📎 Read more: [{page.title}]({page.url})"
                )
        
        if not summaries:
            return f"Found articles but couldn't retrieve summaries for '{query}'"
        
        result_str = "\n\n---\n\n".join(summaries)
        print(f"DEBUG WIKIPEDIA RETURN:\n{result_str}") # Debug: Print final return string
        return result_str
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Create singleton instance
_wikipedia_tool = WikipediaTool()


@tool
async def wikipedia_search(query: str) -> str:
    """
    Search Wikipedia for information about a topic.
    
    Use this tool when you need factual information from Wikipedia
    to answer questions about general knowledge, science, history,
    technology, or any other topic that might be covered in an encyclopedia.
    
    Args:
        query: The search query to look up on Wikipedia
        
    Returns:
        Summarized information from relevant Wikipedia articles
    """
    return await _wikipedia_tool.search_and_summarize(query)


# Export for direct use
wikipedia_tool = wikipedia_search

"""
Course Materials Search Tool.

Integrates the RAG engine's semantic search into the chat agent,
providing grounded responses with inline citations from course materials.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rag_engine.semantic_search import get_semantic_search, FileSearchResult
from utils.logger import logger


class CourseMaterialsSearchResult(BaseModel):
    """Structured result from course materials search."""

    filename: str
    filepath: str
    file_type: str
    relevance_score: float
    matching_sections: List[Dict[str, Any]]
    citation: str  # Formatted citation string


class CourseMaterialsSearchTool:
    """
    Search tool for course materials using RAG engine.

    Provides:
    - Semantic search over all uploaded course content
    - Inline citations with page/slide/line references
    - Priority over external searches for academic content
    """

    def __init__(self):
        self._search_service = None

    @property
    def search_service(self):
        """Lazy initialization of search service."""
        if self._search_service is None:
            self._search_service = get_semantic_search()
        return self._search_service

    async def search(
        self, query: str, top_k: int = 5, file_type: Optional[str] = None
    ) -> List[CourseMaterialsSearchResult]:
        """
        Search course materials for relevant content.

        Args:
            query: Natural language search query
            top_k: Maximum number of results
            file_type: Optional filter ('pdf', 'pptx', 'code')

        Returns:
            List of search results with citations
        """
        try:
            logger.info(f"[CourseSearch] Searching for: '{query}' (top_k={top_k})")

            results = await self.search_service.search_files(
                query=query,
                top_k=top_k,
                file_type=file_type,
                return_sections=True,
                max_sections_per_file=3,
            )

            formatted_results = []
            for result in results:
                # Generate citation string
                citation = self._format_citation(result)

                formatted_results.append(
                    CourseMaterialsSearchResult(
                        filename=result.filename,
                        filepath=result.filepath,
                        file_type=result.file_type,
                        relevance_score=result.relevance_score,
                        matching_sections=result.matching_sections,
                        citation=citation,
                    )
                )

            logger.info(f"[CourseSearch] Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"[CourseSearch] Search failed: {e}")
            return []

    def _format_citation(self, result: FileSearchResult) -> str:
        """
        Format a citation string for the result.

        Args:
            result: Search result

        Returns:
            Citation string like "[Source: Lecture 2.pptx, Slide 5]"
        """
        filename = result.filename

        if result.matching_sections:
            # Get the most relevant section's location
            section = result.matching_sections[0]
            location = section.get("location", "")
            if location:
                return f"[Source: {filename}, {location}]"

        return f"[Source: {filename}]"

    def format_for_llm(self, results: List[CourseMaterialsSearchResult]) -> str:
        """
        Format search results for LLM consumption.

        Creates a structured context with citations that the LLM
        should reference in its response.

        Args:
            results: List of search results

        Returns:
            Formatted string for LLM context
        """
        if not results:
            return "No relevant course materials found for this query."

        parts = ["**Relevant Course Materials Found:**\n"]

        for i, result in enumerate(results, 1):
            # Header with citation
            parts.append(f"### {i}. {result.filename}")
            parts.append(f"**Citation:** `{result.citation}`")
            parts.append(
                f"**Type:** {result.file_type} | **Relevance:** {min(result.relevance_score * 100, 100):.0f}%"
            )
            parts.append(f"**File Path:** `{result.filepath}`\n")

            # Content from matching sections
            if result.matching_sections:
                for section in result.matching_sections[:2]:  # Limit to 2 sections
                    location = section.get("location", "Unknown location")
                    content = section.get("content_preview", "")
                    if content:
                        parts.append(f"**{location}:**")
                        parts.append(
                            f"> {content[:500]}{'...' if len(content) > 500 else ''}\n"
                        )

            parts.append("---\n")

        # Add instruction for the LLM with enhanced citation format
        parts.append(
            "\n**IMPORTANT:** Use the citations above when referencing this information in your response."
        )
        parts.append(
            "Include extended citations with content preview using this format:"
        )
        parts.append("`[Source: filename, location | content excerpt]`")
        parts.append(
            "Example: `[Source: Lecture 3.pptx, Slide 5 | Binary search divides the sorted array...]`"
        )
        parts.append(
            "\nAt the end of your response, add a Sources section with file links:"
        )
        parts.append("```")
        parts.append("---")
        parts.append("**📚 Sources Used:**")

        from config.settings import settings

        for result in results[:5]:
            # Convert absolute path to served URL
            filepath = result.filepath.replace("\\", "/")

            # Construct URL for served content
            # Files are served at /contents/ relative to base dir
            if "/contents/" in filepath:
                relative_path = filepath.split("/contents/")[-1]
                # Use localhost for development, or configurable URL
                base_url = f"http://{settings.HOST}:{settings.PORT}"
                url = f"{base_url}/contents/{relative_path}"
                parts.append(f"- [{result.filename}]({url})")
            else:
                # Fallback to file path if not in contents dir
                parts.append(f"- [{result.filename}]({filepath})")

        parts.append("```")

        return "\n".join(parts)


# Singleton instance
_course_materials_tool: Optional[CourseMaterialsSearchTool] = None


def _get_course_materials_tool() -> CourseMaterialsSearchTool:
    """Get or create the course materials search tool instance."""
    global _course_materials_tool
    if _course_materials_tool is None:
        _course_materials_tool = CourseMaterialsSearchTool()
    return _course_materials_tool


@tool
async def course_materials_search(query: str, file_type: Optional[str] = None) -> str:
    """
    Search course materials for information relevant to the query.

    This is your PRIMARY source for answering questions about course content.
    ALWAYS use this tool first before searching Wikipedia or the web.

    The course materials include:
    - Lecture slides (PPTX)
    - PDF documents and readings
    - Code files and examples
    - Notes and supplementary materials

    Args:
        query: What to search for in course materials
        file_type: Optional filter - 'pdf', 'pptx', or 'code'

    Returns:
        Relevant content from course materials with citations.
        Use the provided citations in your response.
    """
    tool_instance = _get_course_materials_tool()
    results = await tool_instance.search(query, top_k=5, file_type=file_type)
    return tool_instance.format_for_llm(results)


# Export for use in agent
course_materials_search_tool = course_materials_search
get_course_materials_tool = _get_course_materials_tool

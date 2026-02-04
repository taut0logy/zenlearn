"""
Community Bot - AI-powered auto-reply when users are offline.

Uses RAG to generate grounded responses from course materials.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import logger
from services.gemini_service import gemini_service
from rag_engine.semantic_search import get_semantic_search


class CommunityBot:
    """
    AI Bot that generates helpful replies when mentioned users are offline.

    Uses course materials via RAG to provide grounded, accurate responses.
    """

    BOT_SYSTEM_PROMPT = """You are a helpful AI teaching assistant for a university course platform.
A student has asked a question and the person they mentioned is currently unavailable.

Your task is to provide a helpful, grounded response based on the course materials and context.

Guidelines:
1. Be helpful and educational
2. **ALWAYS cite sources** when using information from course materials
3. Use inline citations: `[Source: filename, location]`
4. Be concise but thorough
5. If you're not sure about something, say so
6. Encourage the student to follow up when the mentioned person is available
7. Use markdown formatting for clarity

When citing course materials, use this format:
- Inline: "Binary search has O(log n) complexity [Source: Lecture 3.pptx, Slide 12]"
- Add a Sources section at the end with all references

Start your response with "🤖 **Auto-Reply** (The mentioned user is currently offline)\\n\\n"
"""

    def __init__(self, db: AsyncSession):
        self._search_service = None
        self.db = db

    @property
    def search_service(self):
        """Lazy initialization of semantic search service."""
        if self._search_service is None:
            self._search_service = get_semantic_search()
        return self._search_service

    async def _search_course_materials(
        self, query: str, course_topic: Optional[str] = None, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search course materials for relevant content using RAG.

        Args:
            query: The question/topic to search for
            course_topic: Optional course topic filter
            top_k: Maximum number of results

        Returns:
            List of search results with content and citations
        """
        try:
            # Enhance query with course topic if available
            search_query = query
            if course_topic:
                search_query = f"{course_topic}: {query}"

            logger.info(f"[CommunityBot] RAG search: '{search_query[:50]}...'")

            results = await self.search_service.search_files(
                query=search_query,
                top_k=top_k,
                return_sections=True,
                max_sections_per_file=2,
            )

            formatted_results = []
            for result in results:
                citation = self._format_citation(result)
                formatted_results.append(
                    {
                        "filename": result.filename,
                        "file_type": result.file_type,
                        "relevance_score": result.relevance_score,
                        "citation": citation,
                        "sections": result.matching_sections[:2]
                        if result.matching_sections
                        else [],
                    }
                )

            logger.info(f"[CommunityBot] Found {len(formatted_results)} RAG results")
            return formatted_results

        except Exception as e:
            logger.error(f"[CommunityBot] RAG search failed: {e}")
            return []

    def _format_citation(self, result) -> str:
        """Format a citation string for a search result."""
        filename = result.filename
        if result.matching_sections:
            section = result.matching_sections[0]
            location = section.get("location", "")
            if location:
                return f"[Source: {filename}, {location}]"
        return f"[Source: {filename}]"

    def _format_rag_context(self, rag_results: List[Dict[str, Any]]) -> str:
        """
        Format RAG results into grounded context for the LLM.

        Args:
            rag_results: List of search results

        Returns:
            Formatted context string with citations
        """
        if not rag_results:
            return ""

        parts = [
            "\n## 📚 Relevant Course Materials (USE THESE FOR GROUNDED RESPONSE):\n"
        ]

        for i, result in enumerate(rag_results, 1):
            parts.append(f"### {i}. {result['filename']}")
            parts.append(f"**Citation:** `{result['citation']}`")
            parts.append(
                f"**Relevance:** {min(result['relevance_score'] * 100, 100):.0f}%\n"
            )

            for section in result.get("sections", []):
                location = section.get("location", "")
                content = section.get("content_preview", "")
                if content:
                    parts.append(f"**{location}:**")
                    parts.append(
                        f"> {content[:400]}{'...' if len(content) > 400 else ''}\n"
                    )

            parts.append("---")

        parts.append(
            "\n**IMPORTANT:** Cite these sources in your response using `[Source: filename, location]` format."
        )
        parts.append(
            "Add a Sources section at the end listing all referenced materials.\n"
        )

        return "\n".join(parts)

    async def generate_reply(
        self, post_id: UUID, parent_comment_id: UUID, question_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an AI reply to a comment when the mentioned user is offline.

        Args:
            post_id: The post ID
            parent_comment_id: The comment being replied to
            question_content: The question/comment text

        Returns:
            The created bot comment data, or None if generation failed
        """
        try:
            # Get post context
            post_context = await self._get_post_context(post_id)

            # Search course materials for grounded response
            rag_results = await self._search_course_materials(
                query=question_content, course_topic=post_context.get("course_topic")
            )

            # Format RAG context
            rag_context = self._format_rag_context(rag_results)

            # Build prompt with RAG grounding
            prompt = self._build_prompt(question_content, post_context, rag_context)

            # Generate response using Gemini
            response = await gemini_service.generate(prompt)

            if not response:
                logger.warning("Empty response from Gemini for bot reply")
                return None

            # Extract source citations for metadata
            source_citations = [r["citation"] for r in rag_results]

            # Create bot comment
            bot_comment = await self._save_bot_comment(
                post_id=post_id,
                parent_id=parent_comment_id,
                content=response,
                metadata={
                    "course_topic": post_context.get("course_topic"),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model": "gemini",
                    "grounded": len(rag_results) > 0,
                    "sources": source_citations,
                },
            )

            logger.info(
                f"Generated grounded bot reply for post {post_id} with {len(rag_results)} sources"
            )
            return bot_comment

        except Exception as e:
            logger.error(f"Error generating bot reply: {e}")
            return None

    async def generate_post_reply(
        self,
        post_id: UUID,
        title: str,
        content: str,
        category: str,
        course_topic: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an AI reply to a new post automatically.

        Args:
            post_id: The post ID
            title: Post title
            content: Post content
            category: Post category
            course_topic: Optional course topic

        Returns:
            The created bot comment data, or None if generation failed
        """
        try:
            logger.info(f"Bot: Starting auto-reply for post {post_id}")
            logger.info(f"Bot: Post title: {title[:50]}...")

            # Build context from post data
            post_context = {
                "title": title,
                "content": content[:2000],  # Limit context size
                "course_topic": course_topic,
                "category": category,
            }

            # Search course materials for grounded response
            search_query = f"{title} {content[:500]}"
            rag_results = await self._search_course_materials(
                query=search_query, course_topic=course_topic
            )

            # Format RAG context
            rag_context = self._format_rag_context(rag_results)

            # Build prompt for initial post reply with RAG grounding
            prompt = self._build_post_reply_prompt(post_context, rag_context)
            logger.info(
                f"Bot: Built prompt with {len(rag_results)} RAG sources, calling Gemini..."
            )

            # Generate response using Gemini
            response = await gemini_service.generate(prompt)
            logger.info(
                f"Bot: Gemini response received, length: {len(response) if response else 0}"
            )

            if not response:
                logger.warning("Empty response from Gemini for post auto-reply")
                return None

            # Extract source citations for metadata
            source_citations = [r["citation"] for r in rag_results]

            # Create bot comment (no parent - direct reply to post)
            logger.info(f"Bot: Saving bot comment to database...")
            bot_comment = await self._save_bot_comment(
                post_id=post_id,
                parent_id=None,
                content=response,
                metadata={
                    "course_topic": course_topic,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model": "gemini",
                    "auto_reply": True,
                    "grounded": len(rag_results) > 0,
                    "sources": source_citations,
                },
            )

            logger.info(
                f"Generated grounded auto bot reply for new post {post_id} with {len(rag_results)} sources"
            )
            return bot_comment

        except Exception as e:
            logger.error(f"Error generating post auto-reply: {e}", exc_info=True)
            return None

    def _build_post_reply_prompt(
        self, post_context: Dict[str, Any], rag_context: str = ""
    ) -> str:
        """Build the prompt for auto-replying to a new post with RAG grounding."""
        system_prompt = """You are ZenLearn Bot, a helpful AI teaching assistant for a university course platform.
A student has just posted a question or discussion topic. Provide a helpful initial response.

Guidelines:
1. Be welcoming and encouraging
2. If it's a question, try to provide a helpful answer or point them in the right direction
3. **ALWAYS cite sources** when using information from course materials
4. Use inline citations: `[Source: filename, location]`
5. If you're not sure, acknowledge that and suggest they wait for other community members
6. Be concise but thorough
7. Use markdown formatting for clarity
8. If it's a theory topic, explain concepts clearly with citations
9. If it's a lab topic, you can suggest debugging approaches or resources

When citing course materials, use this format:
- Inline: "This concept relates to... [Source: Lecture 3.pptx, Slide 12]"
- Add a Sources section at the end with all references

Start your response with "🤖 **ZenLearn Bot**\\n\\n"
"""

        context_parts = []

        if post_context.get("title"):
            context_parts.append(f"**Post Title:** {post_context['title']}")

        if post_context.get("course_topic"):
            context_parts.append(f"**Course Topic:** {post_context['course_topic']}")

        if post_context.get("category"):
            context_parts.append(f"**Category:** {post_context['category']}")

        if post_context.get("content"):
            context_parts.append(f"**Post Content:**\n{post_context['content']}")

        context = "\n".join(context_parts)

        return f"""{system_prompt}

## New Post Details
{context}
{rag_context}

## Your Response
Provide a helpful, grounded response to this post:"""

    async def _get_post_context(self, post_id: UUID) -> Dict[str, Any]:
        """Get context from the post for better replies."""
        query = """
            SELECT title, content, course_topic, category
            FROM community_posts
            WHERE id = :post_id
        """
        result = await self.db.execute(text(query), {"post_id": str(post_id)})
        row = result.fetchone()

        if not row:
            return {}

        return {
            "title": row.title,
            "content": row.content[:1000],  # Limit context size
            "course_topic": row.course_topic,
            "category": row.category,
        }

    def _build_prompt(
        self, question: str, post_context: Dict[str, Any], rag_context: str = ""
    ) -> str:
        """Build the prompt for Gemini with RAG grounding."""
        context_parts = []

        if post_context.get("title"):
            context_parts.append(f"**Post Title:** {post_context['title']}")

        if post_context.get("course_topic"):
            context_parts.append(f"**Course Topic:** {post_context['course_topic']}")

        if post_context.get("category"):
            context_parts.append(f"**Category:** {post_context['category']}")

        if post_context.get("content"):
            context_parts.append(f"**Original Post:**\n{post_context['content']}")

        context = (
            "\n".join(context_parts)
            if context_parts
            else "No additional context available."
        )

        return f"""{self.BOT_SYSTEM_PROMPT}

## Context
{context}
{rag_context}

## Student's Question/Comment
{question}

## Your Response
Provide a helpful, grounded response:"""

    async def _save_bot_comment(
        self, post_id: UUID, parent_id: UUID, content: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save the bot's comment to the database."""
        import json

        query = """
            INSERT INTO community_comments 
            (post_id, author_id, parent_id, content, is_bot_reply, bot_metadata)
            VALUES (:post_id, NULL, :parent_id, :content, true, :bot_metadata)
            RETURNING id, post_id, parent_id, content, is_bot_reply, bot_metadata, created_at
        """
        result = await self.db.execute(
            text(query),
            {
                "post_id": str(post_id),
                "parent_id": str(parent_id) if parent_id else None,
                "content": content,
                "bot_metadata": json.dumps(metadata),
            },
        )
        row = result.fetchone()
        await self.db.commit()

        logger.info(f"Bot comment saved successfully: {row.id}")

        return {
            "id": row.id,
            "post_id": row.post_id,
            "parent_id": row.parent_id,
            "content": row.content,
            "is_bot_reply": row.is_bot_reply,
            "bot_metadata": metadata,
            "created_at": row.created_at,
        }

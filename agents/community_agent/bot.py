"""
Community Bot - AI-powered auto-reply when users are offline.

Uses RAG to generate grounded responses from course materials.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.logger import logger
from services.gemini_service import gemini_service


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
2. If you reference specific course content, mention it clearly
3. Be concise but thorough
4. If you're not sure about something, say so
5. Encourage the student to follow up when the mentioned person is available
6. Use markdown formatting for clarity

Start your response with "🤖 **Auto-Reply** (The mentioned user is currently offline)\\n\\n"
"""

    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_reply(
        self,
        post_id: UUID,
        parent_comment_id: UUID,
        question_content: str
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
            
            # Build prompt
            prompt = self._build_prompt(question_content, post_context)
            
            # Generate response using Gemini
            response = await gemini_service.generate_response(prompt)
            
            if not response:
                logger.warning("Empty response from Gemini for bot reply")
                return None
            
            # Create bot comment
            bot_comment = await self._save_bot_comment(
                post_id=post_id,
                parent_id=parent_comment_id,
                content=response,
                metadata={
                    "course_topic": post_context.get("course_topic"),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model": "gemini",
                    "sources": []  # TODO: Add RAG sources when integrated
                }
            )
            
            logger.info(f"Generated bot reply for post {post_id}")
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
        course_topic: Optional[str] = None
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
                "category": category
            }
            
            # Build prompt for initial post reply
            prompt = self._build_post_reply_prompt(post_context)
            logger.info(f"Bot: Built prompt, calling Gemini...")
            
            # Generate response using Gemini
            response = await gemini_service.generate_response(prompt)
            logger.info(f"Bot: Gemini response received, length: {len(response) if response else 0}")
            
            if not response:
                logger.warning("Empty response from Gemini for post auto-reply")
                return None
            
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
                    "sources": []
                }
            )
            
            logger.info(f"Generated auto bot reply for new post {post_id}")
            return bot_comment
            
        except Exception as e:
            logger.error(f"Error generating post auto-reply: {e}", exc_info=True)
            return None
    
    def _build_post_reply_prompt(self, post_context: Dict[str, Any]) -> str:
        """Build the prompt for auto-replying to a new post."""
        system_prompt = """You are ZenLearn Bot, a helpful AI teaching assistant for a university course platform.
A student has just posted a question or discussion topic. Provide a helpful initial response.

Guidelines:
1. Be welcoming and encouraging
2. If it's a question, try to provide a helpful answer or point them in the right direction
3. If you're not sure, acknowledge that and suggest they wait for other community members
4. Be concise but thorough
5. Use markdown formatting for clarity
6. If it's a theory topic, explain concepts clearly
7. If it's a lab topic, you can suggest debugging approaches or resources

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

## Your Response
Provide a helpful response to this post:"""
    
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
            "category": row.category
        }
    
    def _build_prompt(self, question: str, post_context: Dict[str, Any]) -> str:
        """Build the prompt for Gemini."""
        context_parts = []
        
        if post_context.get("title"):
            context_parts.append(f"**Post Title:** {post_context['title']}")
        
        if post_context.get("course_topic"):
            context_parts.append(f"**Course Topic:** {post_context['course_topic']}")
        
        if post_context.get("category"):
            context_parts.append(f"**Category:** {post_context['category']}")
        
        if post_context.get("content"):
            context_parts.append(f"**Original Post:**\n{post_context['content']}")
        
        context = "\n".join(context_parts) if context_parts else "No additional context available."
        
        return f"""{self.BOT_SYSTEM_PROMPT}

## Context
{context}

## Student's Question/Comment
{question}

## Your Response
Provide a helpful response:"""
    
    async def _save_bot_comment(
        self,
        post_id: UUID,
        parent_id: UUID,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save the bot's comment to the database."""
        import json
        
        query = """
            INSERT INTO community_comments 
            (post_id, author_id, parent_id, content, is_bot_reply, bot_metadata)
            VALUES (:post_id, NULL, :parent_id, :content, true, :bot_metadata)
            RETURNING id, post_id, parent_id, content, is_bot_reply, bot_metadata, created_at
        """
        result = await self.db.execute(text(query), {
            "post_id": str(post_id),
            "parent_id": str(parent_id) if parent_id else None,
            "content": content,
            "bot_metadata": json.dumps(metadata)
        })
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
            "created_at": row.created_at
        }

"""
Community Service - Business logic for community operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, or_, and_, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from utils.logger import logger
from .schemas import (
    PostCreate, PostUpdate, PostResponse, PostDetailResponse, PostListResponse,
    CommentCreate, CommentResponse, PostCategory, AuthorInfo,
    PresenceStatus
)


class CommunityService:
    """Service for community operations."""
    
    # Presence thresholds
    ONLINE_THRESHOLD_MINUTES = 2
    AWAY_THRESHOLD_MINUTES = 10
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_posts(
        self,
        category: Optional[PostCategory] = None,
        course_topic: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PostListResponse:
        """List posts with filters and pagination."""
        # Build WHERE clause
        where_clauses = ["1=1"]
        params = {}
        
        if category:
            where_clauses.append("p.category = :category")
            params["category"] = category.value
        
        if course_topic:
            where_clauses.append("p.course_topic ILIKE :course_topic")
            params["course_topic"] = f"%{course_topic}%"
        
        if is_resolved is not None:
            where_clauses.append("p.is_resolved = :is_resolved")
            params["is_resolved"] = is_resolved
        
        if search:
            where_clauses.append("(p.title ILIKE :search OR p.content ILIKE :search)")
            params["search"] = f"%{search}%"
        
        where_sql = " AND ".join(where_clauses)
        
        # Count query (simple)
        count_query = f"SELECT COUNT(*) FROM community_posts p WHERE {where_sql}"
        total_result = await self.db.execute(text(count_query), params)
        total = total_result.scalar() or 0
        
        # Main query with pagination
        query = f"""
            SELECT 
                p.id, p.author_id, p.title, p.content, p.category,
                p.course_topic, p.is_resolved, p.view_count,
                p.created_at, p.updated_at,
                pr.name as author_name, pr.avatar_url as author_avatar,
                (SELECT COUNT(*) FROM community_comments c WHERE c.post_id = p.id) as comment_count
            FROM community_posts p
            LEFT JOIN profiles pr ON p.author_id = pr.id
            WHERE {where_sql}
            ORDER BY p.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        posts = []
        for row in rows:
            posts.append(PostResponse(
                id=row.id,
                author=AuthorInfo(
                    id=row.author_id,
                    name=row.author_name or "Unknown",
                    avatar_url=row.author_avatar
                ),
                title=row.title,
                content=row.content[:500] + "..." if len(row.content) > 500 else row.content,
                category=PostCategory(row.category),
                course_topic=row.course_topic,
                is_resolved=row.is_resolved,
                view_count=row.view_count,
                comment_count=row.comment_count,
                created_at=row.created_at,
                updated_at=row.updated_at
            ))
        
        return PostListResponse(
            posts=posts,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total
        )
    
    async def create_post(self, user_id: UUID, post_data: PostCreate) -> PostResponse:
        """Create a new post."""
        from .bot import CommunityBot
        
        query = """
            INSERT INTO community_posts (author_id, title, content, category, course_topic)
            VALUES (:author_id, :title, :content, :category, :course_topic)
            RETURNING id, author_id, title, content, category, course_topic, 
                      is_resolved, view_count, created_at, updated_at
        """
        result = await self.db.execute(text(query), {
            "author_id": str(user_id),
            "title": post_data.title,
            "content": post_data.content,
            "category": post_data.category.value,
            "course_topic": post_data.course_topic
        })
        row = result.fetchone()
        await self.db.commit()
        
        # Get author info
        author_result = await self.db.execute(
            text("SELECT name, avatar_url FROM profiles WHERE id = :id"),
            {"id": str(user_id)}
        )
        author_row = author_result.fetchone()
        
        post_response = PostResponse(
            id=row.id,
            author=AuthorInfo(
                id=user_id,
                name=author_row.name if author_row else "Unknown",
                avatar_url=author_row.avatar_url if author_row else None
            ),
            title=row.title,
            content=row.content,
            category=PostCategory(row.category),
            course_topic=row.course_topic,
            is_resolved=row.is_resolved,
            view_count=row.view_count,
            comment_count=0,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
        
        # Trigger bot auto-reply for the new post
        try:
            bot = CommunityBot(self.db)
            await bot.generate_post_reply(
                post_id=row.id,
                title=post_data.title,
                content=post_data.content,
                category=post_data.category.value,
                course_topic=post_data.course_topic
            )
            logger.info(f"Bot auto-reply triggered for post {row.id}")
        except Exception as e:
            logger.error(f"Error triggering bot auto-reply: {e}")
        
        return post_response
    
    async def get_post_with_comments(self, post_id: UUID) -> Optional[PostDetailResponse]:
        """Get a post with all comments."""
        # Get post
        post_query = """
            SELECT 
                p.id, p.author_id, p.title, p.content, p.category,
                p.course_topic, p.is_resolved, p.view_count,
                p.created_at, p.updated_at,
                pr.name as author_name, pr.avatar_url as author_avatar
            FROM community_posts p
            LEFT JOIN profiles pr ON p.author_id = pr.id
            WHERE p.id = :post_id
        """
        result = await self.db.execute(text(post_query), {"post_id": str(post_id)})
        post_row = result.fetchone()
        
        if not post_row:
            return None
        
        # Increment view count
        await self.db.execute(
            text("UPDATE community_posts SET view_count = view_count + 1 WHERE id = :id"),
            {"id": str(post_id)}
        )
        await self.db.commit()
        
        # Get comments
        comments_query = """
            SELECT 
                c.id, c.post_id, c.author_id, c.parent_id, c.content,
                c.is_bot_reply, c.mentioned_user_id, c.bot_metadata, c.created_at,
                pr.name as author_name, pr.avatar_url as author_avatar
            FROM community_comments c
            LEFT JOIN profiles pr ON c.author_id = pr.id
            WHERE c.post_id = :post_id
            ORDER BY c.created_at ASC
        """
        comments_result = await self.db.execute(text(comments_query), {"post_id": str(post_id)})
        comment_rows = comments_result.fetchall()
        
        # Build comment tree
        comments_map = {}
        root_comments = []
        
        for row in comment_rows:
            comment = CommentResponse(
                id=row.id,
                post_id=row.post_id,
                author=AuthorInfo(
                    id=row.author_id,
                    name=row.author_name or "Bot",
                    avatar_url=row.author_avatar
                ) if row.author_id else None,
                parent_id=row.parent_id,
                content=row.content,
                is_bot_reply=row.is_bot_reply,
                mentioned_user_id=row.mentioned_user_id,
                bot_metadata=row.bot_metadata,
                created_at=row.created_at,
                replies=[]
            )
            comments_map[row.id] = comment
            
            if row.parent_id is None:
                root_comments.append(comment)
            else:
                parent = comments_map.get(row.parent_id)
                if parent:
                    parent.replies.append(comment)
        
        return PostDetailResponse(
            id=post_row.id,
            author=AuthorInfo(
                id=post_row.author_id,
                name=post_row.author_name or "Unknown",
                avatar_url=post_row.author_avatar
            ),
            title=post_row.title,
            content=post_row.content,
            category=PostCategory(post_row.category),
            course_topic=post_row.course_topic,
            is_resolved=post_row.is_resolved,
            view_count=post_row.view_count + 1,
            created_at=post_row.created_at,
            updated_at=post_row.updated_at,
            comments=root_comments
        )
    
    async def update_post(
        self, 
        post_id: UUID, 
        user_id: UUID, 
        post_data: PostUpdate
    ) -> Optional[PostResponse]:
        """Update a post (author only)."""
        # Check ownership
        check = await self.db.execute(
            text("SELECT author_id FROM community_posts WHERE id = :id"),
            {"id": str(post_id)}
        )
        row = check.fetchone()
        if not row or row.author_id != user_id:
            return None
        
        # Build update
        updates = []
        params = {"id": str(post_id)}
        
        if post_data.title is not None:
            updates.append("title = :title")
            params["title"] = post_data.title
        if post_data.content is not None:
            updates.append("content = :content")
            params["content"] = post_data.content
        if post_data.category is not None:
            updates.append("category = :category")
            params["category"] = post_data.category.value
        if post_data.course_topic is not None:
            updates.append("course_topic = :course_topic")
            params["course_topic"] = post_data.course_topic
        if post_data.is_resolved is not None:
            updates.append("is_resolved = :is_resolved")
            params["is_resolved"] = post_data.is_resolved
        
        if updates:
            updates.append("updated_at = NOW()")
            query = f"UPDATE community_posts SET {', '.join(updates)} WHERE id = :id"
            await self.db.execute(text(query), params)
            await self.db.commit()
        
        # Return updated post
        return await self._get_post_response(post_id)
    
    async def delete_post(self, post_id: UUID, user_id: UUID) -> bool:
        """Delete a post (author only)."""
        result = await self.db.execute(
            text("DELETE FROM community_posts WHERE id = :id AND author_id = :author_id"),
            {"id": str(post_id), "author_id": str(user_id)}
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def toggle_resolved(self, post_id: UUID, user_id: UUID) -> Optional[PostResponse]:
        """Toggle resolved status."""
        await self.db.execute(
            text("""UPDATE community_posts 
               SET is_resolved = NOT is_resolved, updated_at = NOW() 
               WHERE id = :id AND author_id = :author_id"""),
            {"id": str(post_id), "author_id": str(user_id)}
        )
        await self.db.commit()
        return await self._get_post_response(post_id)
    
    async def create_comment(
        self, 
        post_id: UUID, 
        user_id: UUID, 
        comment_data: CommentCreate
    ) -> CommentResponse:
        """Create a comment, potentially triggering bot reply."""
        from .bot import CommunityBot
        
        # Insert comment
        query = """
            INSERT INTO community_comments 
            (post_id, author_id, parent_id, content, mentioned_user_id)
            VALUES (:post_id, :author_id, :parent_id, :content, :mentioned_user_id)
            RETURNING id, post_id, author_id, parent_id, content, 
                      is_bot_reply, mentioned_user_id, bot_metadata, created_at
        """
        result = await self.db.execute(text(query), {
            "post_id": str(post_id),
            "author_id": str(user_id),
            "parent_id": str(comment_data.parent_id) if comment_data.parent_id else None,
            "content": comment_data.content,
            "mentioned_user_id": str(comment_data.mentioned_user_id) if comment_data.mentioned_user_id else None
        })
        row = result.fetchone()
        await self.db.commit()
        
        # Get author info
        author_result = await self.db.execute(
            text("SELECT name, avatar_url FROM profiles WHERE id = :id"),
            {"id": str(user_id)}
        )
        author_row = author_result.fetchone()
        
        comment = CommentResponse(
            id=row.id,
            post_id=row.post_id,
            author=AuthorInfo(
                id=user_id,
                name=author_row.name if author_row else "Unknown",
                avatar_url=author_row.avatar_url if author_row else None
            ),
            parent_id=row.parent_id,
            content=row.content,
            is_bot_reply=False,
            mentioned_user_id=row.mentioned_user_id,
            bot_metadata=None,
            created_at=row.created_at,
            replies=[]
        )
        
        # Check if we need to trigger bot reply
        if comment_data.mentioned_user_id:
            is_offline = await self._is_user_offline(comment_data.mentioned_user_id)
            if is_offline:
                logger.info(f"User {comment_data.mentioned_user_id} is offline, triggering bot reply")
                try:
                    bot = CommunityBot(self.db)
                    await bot.generate_reply(post_id, row.id, comment_data.content)
                except Exception as e:
                    logger.error(f"Error generating bot reply: {e}")
        
        return comment
    
    async def delete_comment(self, comment_id: UUID, user_id: UUID) -> bool:
        """Delete a comment (author only)."""
        result = await self.db.execute(
            text("DELETE FROM community_comments WHERE id = :id AND author_id = :author_id"),
            {"id": str(comment_id), "author_id": str(user_id)}
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def update_presence(self, user_id: UUID) -> PresenceStatus:
        """Update user presence (heartbeat)."""
        query = """
            INSERT INTO user_presence (user_id, last_seen, is_online)
            VALUES (:user_id, NOW(), true)
            ON CONFLICT (user_id) 
            DO UPDATE SET last_seen = NOW(), is_online = true
            RETURNING user_id, last_seen, is_online
        """
        result = await self.db.execute(text(query), {"user_id": str(user_id)})
        row = result.fetchone()
        await self.db.commit()
        
        return PresenceStatus(
            user_id=row.user_id,
            is_online=row.is_online,
            last_seen=row.last_seen
        )
    
    async def get_users_presence(self, user_ids: List[UUID]) -> List[PresenceStatus]:
        """Get presence status for multiple users."""
        if not user_ids:
            return []
        
        placeholders = ", ".join([f":id{i}" for i in range(len(user_ids))])
        params = {f"id{i}": str(uid) for i, uid in enumerate(user_ids)}
        
        query = f"""
            SELECT user_id, last_seen, is_online,
                   CASE 
                       WHEN last_seen > NOW() - INTERVAL '{self.ONLINE_THRESHOLD_MINUTES} minutes' THEN true
                       ELSE false
                   END as actually_online
            FROM user_presence
            WHERE user_id IN ({placeholders})
        """
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        return [
            PresenceStatus(
                user_id=row.user_id,
                is_online=row.actually_online,
                last_seen=row.last_seen
            )
            for row in rows
        ]
    
    async def _is_user_offline(self, user_id: UUID) -> bool:
        """Check if a user is currently offline."""
        query = """
            SELECT last_seen
            FROM user_presence
            WHERE user_id = :user_id
        """
        result = await self.db.execute(text(query), {"user_id": str(user_id)})
        row = result.fetchone()
        
        if not row:
            return True  # No presence record = offline
        
        threshold = datetime.now(timezone.utc) - timedelta(minutes=self.ONLINE_THRESHOLD_MINUTES)
        return row.last_seen < threshold
    
    async def _get_post_response(self, post_id: UUID) -> Optional[PostResponse]:
        """Helper to get post response."""
        query = """
            SELECT 
                p.id, p.author_id, p.title, p.content, p.category,
                p.course_topic, p.is_resolved, p.view_count,
                p.created_at, p.updated_at,
                pr.name as author_name, pr.avatar_url as author_avatar,
                COUNT(c.id) as comment_count
            FROM community_posts p
            LEFT JOIN profiles pr ON p.author_id = pr.id
            LEFT JOIN community_comments c ON c.post_id = p.id
            WHERE p.id = :post_id
            GROUP BY p.id, pr.name, pr.avatar_url
        """
        result = await self.db.execute(text(query), {"post_id": str(post_id)})
        row = result.fetchone()
        
        if not row:
            return None
        
        return PostResponse(
            id=row.id,
            author=AuthorInfo(
                id=row.author_id,
                name=row.author_name or "Unknown",
                avatar_url=row.author_avatar
            ),
            title=row.title,
            content=row.content,
            category=PostCategory(row.category),
            course_topic=row.course_topic,
            is_resolved=row.is_resolved,
            view_count=row.view_count,
            comment_count=row.comment_count,
            created_at=row.created_at,
            updated_at=row.updated_at
        )

"""
Community API Router - Endpoints for community discussion forum.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from utils.logger import logger
from .schemas import (
    PostCreate, PostUpdate, PostResponse, PostDetailResponse, PostListResponse,
    CommentCreate, CommentResponse, PostCategory,
    PresenceHeartbeat, PresenceStatus, UserPresenceList
)
from .service import CommunityService

router = APIRouter(prefix="/community", tags=["Community"])


# ============ Posts Endpoints ============

@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    category: Optional[PostCategory] = Query(None, description="Filter by category"),
    course_topic: Optional[str] = Query(None, description="Filter by course topic"),
    is_resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """List community posts with optional filters."""
    service = CommunityService(db)
    return await service.list_posts(
        category=category,
        course_topic=course_topic,
        is_resolved=is_resolved,
        search=search,
        page=page,
        page_size=page_size
    )


@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    post_data: PostCreate,
    user_id: UUID = Query(..., description="Author user ID"),  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """Create a new community post."""
    service = CommunityService(db)
    try:
        return await service.create_post(user_id, post_data)
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/{post_id}", response_model=PostDetailResponse)
async def get_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a post with all its comments."""
    service = CommunityService(db)
    post = await service.get_post_with_comments(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    post_data: PostUpdate,
    user_id: UUID = Query(..., description="User ID"),  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """Update a post. Only the author can update."""
    service = CommunityService(db)
    post = await service.update_post(post_id, user_id, post_data)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    return post


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: UUID,
    user_id: UUID = Query(..., description="User ID"),  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """Delete a post. Only the author can delete."""
    service = CommunityService(db)
    success = await service.delete_post(post_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")


@router.patch("/posts/{post_id}/resolve", response_model=PostResponse)
async def resolve_post(
    post_id: UUID,
    user_id: UUID = Query(..., description="User ID"),  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """Mark a post as resolved."""
    service = CommunityService(db)
    post = await service.toggle_resolved(post_id, user_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    return post


# ============ Comments Endpoints ============

@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: UUID,
    comment_data: CommentCreate,
    user_id: UUID = Query(..., description="Author user ID"),  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """Add a comment to a post. May trigger bot reply if mentioned user is offline."""
    service = CommunityService(db)
    try:
        comment = await service.create_comment(post_id, user_id, comment_data)
        return comment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: UUID,
    user_id: UUID = Query(..., description="User ID"),  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """Delete a comment. Only the author can delete."""
    service = CommunityService(db)
    success = await service.delete_comment(comment_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found or not authorized")


# ============ Presence Endpoints ============

@router.post("/presence/heartbeat", response_model=PresenceStatus)
async def update_presence(
    user_id: UUID = Query(..., description="User ID"),  # TODO: Get from auth
    db: AsyncSession = Depends(get_db)
):
    """Update user presence (heartbeat). Call every 30 seconds."""
    service = CommunityService(db)
    return await service.update_presence(user_id)


@router.get("/presence/users", response_model=UserPresenceList)
async def get_users_presence(
    user_ids: str = Query(..., description="Comma-separated user IDs"),
    db: AsyncSession = Depends(get_db)
):
    """Get presence status for multiple users."""
    service = CommunityService(db)
    ids = [UUID(id.strip()) for id in user_ids.split(",") if id.strip()]
    statuses = await service.get_users_presence(ids)
    return UserPresenceList(users=statuses)

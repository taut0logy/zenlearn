import os
import shutil
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.settings import settings
from cms_agent.models import Course, Tag, CourseMaterial
from cms_agent.schemas import CourseCreate, CourseMaterialCreate, CourseMaterialUpdate

# Ensure content directory exists
CONTENT_DIR = Path(settings.BASE_DIR) / "contents"
CONTENT_DIR.mkdir(parents=True, exist_ok=True)


class CMSService:
    @staticmethod
    async def create_course(db: AsyncSession, course_in: CourseCreate) -> Course:
        # Check if course_no exists
        stmt = select(Course).where(Course.course_no == course_in.course_no)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Course number already exists")

        course = Course(
            name=course_in.name,
            course_no=course_in.course_no,
            description=course_in.description,
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    @staticmethod
    async def get_courses(db: AsyncSession) -> List[Course]:
        stmt = select(Course).order_by(Course.course_no)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_course(db: AsyncSession, course_id: UUID) -> Optional[Course]:
        stmt = select(Course).where(Course.id == course_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_tags(db: AsyncSession, tag_names: List[str]) -> List[Tag]:
        if not tag_names:
            return []

        # Find existing
        stmt = select(Tag).where(Tag.name.in_(tag_names))
        result = await db.execute(stmt)
        existing_tags = result.scalars().all()
        existing_names = {t.name for t in existing_tags}

        # Create new
        new_tags = []
        for name in tag_names:
            if name not in existing_names:
                new_tag = Tag(name=name)
                db.add(new_tag)
                new_tags.append(new_tag)

        # We need to commit to get IDs for new tags if we were to return them fully populated immediately,
        # but db.add schedules them.
        # Ideally we flush to get them ready for association.
        if new_tags:
            await db.flush()

        return list(existing_tags) + new_tags

    @staticmethod
    async def upload_material(
        db: AsyncSession,
        course_id: UUID,
        file: UploadFile,
        material_in: CourseMaterialCreate,
    ) -> CourseMaterial:
        course = await CMSService.get_course(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Prepare file path: contents/course_no/type/filename
        # Sanitize filename to avoid directory traversal
        filename = file.filename or "untitled"
        filename = os.path.basename(filename)

        save_dir = CONTENT_DIR / course.course_no / material_in.type
        save_dir.mkdir(parents=True, exist_ok=True)

        file_path = save_dir / filename

        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to save file: {str(e)}"
            )

        # Handle Tags
        tags = await CMSService.get_or_create_tags(db, material_in.tags)

        # Create Record
        # Rel path for URL
        rel_path = f"/contents/{course.course_no}/{material_in.type}/{filename}"

        material = CourseMaterial(
            course_id=course_id,
            title=material_in.title,
            description=material_in.description,
            type=material_in.type,
            file_type=material_in.file_type,
            url=rel_path,
            week=material_in.week,
            metadata_=material_in.metadata,
            tags=tags,
        )

        db.add(material)
        await db.commit()
        await db.refresh(material)

        # Reload to get populated tags for response
        # Using selectinload to eagerly load tags
        stmt = (
            select(CourseMaterial)
            .where(CourseMaterial.id == material.id)
            .options(selectinload(CourseMaterial.tags))
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def update_material(
        db: AsyncSession,
        material_id: UUID,
        update_data: CourseMaterialUpdate,  # Reusing Create, but technically optional fields handled in router
    ) -> CourseMaterial:
        # We need a proper update schema or dict
        # Since service receives Pydantic model usually, let's assume dict or model
        # For now, let's look up the material
        stmt = (
            select(CourseMaterial)
            .where(CourseMaterial.id == material_id)
            .options(selectinload(CourseMaterial.tags))
        )
        result = await db.execute(stmt)
        material = result.scalar_one_or_none()

        if not material:
            raise HTTPException(status_code=404, detail="Material not found")

        if update_data.title:
            material.title = update_data.title
        if update_data.description:
            material.description = update_data.description
        if update_data.week is not None:
            material.week = update_data.week

        # Update tags if provided
        if update_data.tags is not None:
            tags = await CMSService.get_or_create_tags(db, update_data.tags)
            material.tags = tags

        await db.commit()
        await db.refresh(material)
        return material

    @staticmethod
    async def delete_material(db: AsyncSession, material_id: UUID):
        stmt = (
            select(CourseMaterial)
            .where(CourseMaterial.id == material_id)
            .options(selectinload(CourseMaterial.course))
        )
        result = await db.execute(stmt)
        material = result.scalar_one_or_none()

        if not material:
            raise HTTPException(status_code=404, detail="Material not found")

        # Delete file from disk
        if material.url.startswith("/contents"):
            # Construct absolute path: BASE_DIR + url
            # url: /contents/CS101/theory/file.pdf
            # CONTENT_DIR: /.../contents
            # relative from content dir: CS101/theory/file.pdf
            rel_path = material.url.lstrip("/contents/")
            file_path = CONTENT_DIR / rel_path
            if file_path.exists():
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to delete file: {e}")

        await db.delete(material)
        await db.commit()
        return True

    @staticmethod
    async def get_materials(
        db: AsyncSession, course_id: UUID, type_filter: Optional[str] = None
    ) -> List[CourseMaterial]:
        stmt = (
            select(CourseMaterial)
            .where(CourseMaterial.course_id == course_id)
            .options(selectinload(CourseMaterial.tags))
        )

        if type_filter:
            stmt = stmt.where(CourseMaterial.type == type_filter)

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_recent_materials(
        db: AsyncSession, limit: int = 20
    ) -> List[CourseMaterial]:
        stmt = (
            select(CourseMaterial)
            .order_by(CourseMaterial.updated_at.desc())
            .limit(limit)
            .options(selectinload(CourseMaterial.tags))
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def delete_materials_by_type(
        db: AsyncSession, course_id: UUID, type_filter: str
    ):
        materials = await CMSService.get_materials(db, course_id, type_filter)
        for material in materials:
            await CMSService.delete_material(db, material.id)
        return True

    @staticmethod
    async def search_tags(db: AsyncSession, query: str = "") -> List[Tag]:
        stmt = select(Tag)
        if query:
            stmt = stmt.where(Tag.name.ilike(f"%{query}%"))
        stmt = stmt.limit(20)
        result = await db.execute(stmt)
        return result.scalars().all()

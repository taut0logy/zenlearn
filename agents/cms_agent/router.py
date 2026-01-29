import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from cms_agent.schemas import (
    CourseCreate,
    CourseResponse,
    CourseMaterialCreate,
    CourseMaterialUpdate,
    CourseMaterialResponse,
    TagResponse,
)
from cms_agent.service import CMSService

router = APIRouter(prefix="/cms", tags=["CMS"])


@router.post(
    "/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED
)
async def create_course(course: CourseCreate, db: AsyncSession = Depends(get_db)):
    return await CMSService.create_course(db, course)


@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db)):
    return await CMSService.get_courses(db)


@router.post("/courses/{course_id}/materials", response_model=CourseMaterialResponse)
async def upload_material(
    course_id: UUID,
    title: str = Form(...),
    type: str = Form(..., description="theory or lab"),
    file_type: str = Form(..., description="pdf, pptx, or code"),
    description: Optional[str] = Form(None),
    tags: str = Form("[]", description="JSON string array of tag names"),
    week: Optional[int] = Form(None, description="Week number"),
    metadata: str = Form("{}", description="JSON string of metadata"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        tags_list = json.loads(tags)
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for tags or metadata")

    material_in = CourseMaterialCreate(
        title=title,
        type=type,
        file_type=file_type,
        description=description,
        tags=tags_list,
        week=week,
        metadata_=metadata_dict,
    )

    return await CMSService.upload_material(db, course_id, file, material_in)


@router.put(
    "/courses/{course_id}/materials/{material_id}",
    response_model=CourseMaterialResponse,
)
async def update_material(
    course_id: UUID,
    material_id: UUID,
    update_data: CourseMaterialUpdate,
    db: AsyncSession = Depends(get_db),
):
    # course_id not strictly needed for update if material_id is unique, but good for validation
    return await CMSService.update_material(db, material_id, update_data)


@router.delete(
    "/courses/{course_id}/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_material(
    course_id: UUID,
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await CMSService.delete_material(db, material_id)
    return None


@router.get("/materials/recent", response_model=List[CourseMaterialResponse])
async def list_recent_materials(limit: int = 20, db: AsyncSession = Depends(get_db)):
    return await CMSService.get_recent_materials(db, limit)


@router.delete("/courses/{course_id}/materials", status_code=status.HTTP_204_NO_CONTENT)
async def delete_materials_by_type(
    course_id: UUID, type: str, db: AsyncSession = Depends(get_db)
):
    await CMSService.delete_materials_by_type(db, course_id, type)
    return None


@router.get("/tags", response_model=List[TagResponse])
async def search_tags(query: str = "", db: AsyncSession = Depends(get_db)):
    return await CMSService.search_tags(db, query)


@router.get(
    "/courses/{course_id}/materials", response_model=List[CourseMaterialResponse]
)
async def list_materials(
    course_id: UUID, type: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    return await CMSService.get_materials(db, course_id, type)

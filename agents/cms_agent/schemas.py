from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: UUID

    class Config:
        from_attributes = True


class CourseBase(BaseModel):
    name: str
    course_no: str
    description: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    course_no: Optional[str] = None
    description: Optional[str] = None


class CourseResponse(CourseBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseMaterialBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str = Field(..., description="theory or lab")
    file_type: str = Field(..., description="pdf, pptx, or code")
    week: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata_")


class CourseMaterialCreate(CourseMaterialBase):
    # url is generated after upload
    tags: List[str] = []  # List of tag names


class CourseMaterialUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    week: Optional[int] = None
    tags: Optional[List[str]] = None


class CourseMaterialResponse(CourseMaterialBase):
    id: UUID
    course_id: UUID
    url: str
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse]

    class Config:
        from_attributes = True

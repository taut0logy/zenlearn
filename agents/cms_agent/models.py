from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import String, ForeignKey, Text, Enum, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from models.base import Base, TimestampMixin

# Association table for Many-to-Many relationship between CourseMaterial and Tag
material_tags = Table(
    "material_tags",
    Base.metadata,
    Column(
        "material_id",
        PG_UUID(as_uuid=True),
        ForeignKey("course_materials.id"),
        primary_key=True,
    ),
    Column("tag_id", PG_UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True),
)


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    course_no: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    materials: Mapped[List["CourseMaterial"]] = relationship(back_populates="course")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)


class CourseMaterial(Base, TimestampMixin):
    __tablename__ = "course_materials"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(
        Enum("theory", "lab", name="course_type"), nullable=False
    )
    file_type: Mapped[str] = mapped_column(
        Enum("pdf", "pptx", "code", name="file_type"), nullable=False
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    week: Mapped[Optional[int]] = mapped_column("week", nullable=True)  # Week number
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )  # Using metadata_ to avoid conflict with Base.metadata

    course: Mapped["Course"] = relationship(back_populates="materials")
    tags: Mapped[List["Tag"]] = relationship(secondary=material_tags)

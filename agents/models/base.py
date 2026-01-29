"""
SQLAlchemy Base model and common mixins.

Provides reusable base classes for all database models with:
- Declarative base
- Timestamp mixin (created_at, updated_at)
- Soft delete mixin (deleted_at)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns.

    Usage:
        class User(Base, TimestampMixin):
            __tablename__ = "users"
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete capability.

    Usage:
        class User(Base, SoftDeleteMixin):
            __tablename__ = "users"
            ...

    To soft delete:
        user.deleted_at = datetime.now(timezone.utc)
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None

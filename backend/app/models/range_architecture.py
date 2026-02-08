"""Range Architecture model - structured range planning."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.season import Season
    from app.models.user import User


class RangeStatus(str, enum.Enum):
    """Range architecture workflow status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    LOCKED = "locked"
    REJECTED = "rejected"


class RangeArchitecture(Base, UUIDPrimaryKeyMixin):
    """Range Architecture for structured range planning.

    Defines the planned assortment dimensions for a season/category
    including price bands, fabric, color families, and style types.
    """

    __tablename__ = "range_architectures"

    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seasons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Range dimensions
    price_band: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fabric: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color_family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    style_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Range metrics
    planned_styles: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    planned_options: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    planned_depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Workflow
    status: Mapped[RangeStatus] = mapped_column(
        Enum(RangeStatus, name="range_status", create_type=True),
        nullable=False,
        default=RangeStatus.DRAFT,
    )

    # Approval fields
    submitted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    review_comment: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="range_architectures")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="range_architectures")
    submitter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[submitted_by])
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])

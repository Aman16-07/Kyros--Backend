"""OTB Adjustment model - tracking rebalancing between categories."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.season import Season
    from app.models.user import User


class AdjustmentStatus(str, enum.Enum):
    """Adjustment approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OTBAdjustment(Base, UUIDPrimaryKeyMixin):
    """OTB Adjustment for rebalancing budget between categories.

    Supports in-season rebalancing with approval workflow,
    rationale documentation, and audit trail.
    """

    __tablename__ = "otb_adjustments"

    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seasons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[AdjustmentStatus] = mapped_column(
        Enum(AdjustmentStatus, name="adjustment_status", create_type=True),
        nullable=False,
        default=AdjustmentStatus.PENDING,
    )

    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="otb_adjustments")
    from_category: Mapped[Optional["Category"]] = relationship(
        "Category", foreign_keys=[from_category_id],
    )
    to_category: Mapped[Optional["Category"]] = relationship(
        "Category", foreign_keys=[to_category_id],
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[approved_by],
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by],
    )

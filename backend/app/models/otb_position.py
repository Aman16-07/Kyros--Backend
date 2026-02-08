"""OTB Position model - dynamic OTB tracking per season/category/month."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.season import Season


class OTBPosition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Dynamic OTB position tracking.

    OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order

    This table tracks the real-time OTB position as POs are placed,
    enabling consumption tracking and alerts.
    """

    __tablename__ = "otb_positions"
    __table_args__ = (
        UniqueConstraint(
            "season_id", "category_id", "month",
            name="uq_otb_position_season_category_month",
        ),
    )

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
    month: Mapped[date] = mapped_column(Date, nullable=False)

    # OTB components
    planned_otb: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False, default=Decimal("0.00"),
    )
    consumed_otb: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False, default=Decimal("0.00"),
    )
    available_otb: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False, default=Decimal("0.00"),
    )

    last_calculated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="otb_positions")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="otb_positions")

    @property
    def consumption_percentage(self) -> Decimal:
        """Percentage of planned OTB that has been consumed."""
        if self.planned_otb and self.planned_otb > 0:
            return round((self.consumed_otb / self.planned_otb) * 100, 2)
        return Decimal("0.00")

    @property
    def is_low(self) -> bool:
        """True if available OTB is below 20% of planned."""
        if self.planned_otb and self.planned_otb > 0:
            return self.available_otb < (self.planned_otb * Decimal("0.20"))
        return False

    @property
    def is_exceeded(self) -> bool:
        """True if consumed exceeds planned."""
        return self.consumed_otb > self.planned_otb

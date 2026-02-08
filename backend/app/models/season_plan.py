"""Season Plan model."""

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SeasonPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Season Plan model for planned sales and margins."""
    
    __tablename__ = "season_plan"
    __table_args__ = (
        UniqueConstraint(
            "season_id", "location_id", "category_id", "sku_id", "version",
            name="uq_season_plan_composite"
        ),
    )
    
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seasons.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    # SKU-level planning support
    sku_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    planned_sales: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    planned_margin: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    # New: Planned units
    planned_units: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    inventory_turns: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    # Historical data: Last Year sales
    ly_sales: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True,
    )
    # Historical data: Last Last Year sales
    lly_sales: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Relationships
    season: Mapped["Season"] = relationship(
        "Season",
        back_populates="season_plans",
    )
    location: Mapped["Location"] = relationship(
        "Location",
        back_populates="season_plans",
    )
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="season_plans",
    )
    uploader: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="uploaded_season_plans",
        foreign_keys=[uploaded_by],
    )
    
    def __repr__(self) -> str:
        return f"<SeasonPlan(id={self.id}, season_id={self.season_id}, version={self.version})>"

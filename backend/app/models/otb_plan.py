"""OTB (Open-To-Buy) Plan model."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OTBPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """OTB Plan model for monthly approved spend limits."""
    
    __tablename__ = "otb_plan"
    __table_args__ = (
        UniqueConstraint(
            "season_id", "location_id", "category_id", "month",
            name="uq_otb_plan_composite"
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
    month: Mapped[date] = mapped_column(Date, nullable=False)
    approved_spend_limit: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    season: Mapped["Season"] = relationship(
        "Season",
        back_populates="otb_plans",
    )
    location: Mapped["Location"] = relationship(
        "Location",
        back_populates="otb_plans",
    )
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="otb_plans",
    )
    uploader: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="uploaded_otb_plans",
        foreign_keys=[uploaded_by],
    )
    
    def __repr__(self) -> str:
        return f"<OTBPlan(id={self.id}, season_id={self.season_id}, month={self.month})>"

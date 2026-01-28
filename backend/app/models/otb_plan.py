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
    """
    OTB Plan model for monthly approved spend limits.
    
    OTB Formula: Planned Sales + Planned Closing Stock - Opening Stock - On Order
    """
    
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
    
    # OTB Formula Components
    planned_sales: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )
    planned_closing_stock: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )
    opening_stock: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )
    on_order: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )
    
    # Calculated OTB value (can be stored or computed)
    approved_spend_limit: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    @property
    def calculated_otb(self) -> Decimal:
        """Calculate OTB: Planned Sales + Planned Closing Stock - Opening Stock - On Order."""
        return (
            self.planned_sales 
            + self.planned_closing_stock 
            - self.opening_stock 
            - self.on_order
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

"""Range Intent model."""

import uuid
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RangeIntent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Range Intent model for category assortment planning."""
    
    __tablename__ = "range_intent"
    __table_args__ = (
        UniqueConstraint(
            "season_id", "category_id",
            name="uq_range_intent_composite"
        ),
    )
    
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seasons.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    core_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
    )
    fashion_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
    )
    price_band_mix: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    season: Mapped["Season"] = relationship(
        "Season",
        back_populates="range_intents",
    )
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="range_intents",
    )
    uploader: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="uploaded_range_intents",
        foreign_keys=[uploaded_by],
    )
    
    def __repr__(self) -> str:
        return f"<RangeIntent(id={self.id}, season_id={self.season_id}, category_id={self.category_id})>"

"""Category model."""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Category model representing product categories with hierarchy."""
    
    __tablename__ = "categories"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Self-referential relationship for category hierarchy
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    
    # Relationships with other models
    season_plans: Mapped[list["SeasonPlan"]] = relationship(
        "SeasonPlan",
        back_populates="category",
    )
    otb_plans: Mapped[list["OTBPlan"]] = relationship(
        "OTBPlan",
        back_populates="category",
    )
    range_intents: Mapped[list["RangeIntent"]] = relationship(
        "RangeIntent",
        back_populates="category",
    )
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="category",
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name}, parent_id={self.parent_id})>"

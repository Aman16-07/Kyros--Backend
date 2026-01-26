"""Purchase Order model."""

import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class POSource(str, enum.Enum):
    """Purchase order source enumeration."""
    
    CSV = "csv"
    API = "api"


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Purchase Order model."""
    
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
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
    po_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    source: Mapped[POSource] = mapped_column(
        Enum(POSource, name="po_source", create_type=True),
        nullable=False,
    )
    
    # Relationships
    season: Mapped["Season"] = relationship(
        "Season",
        back_populates="purchase_orders",
    )
    location: Mapped["Location"] = relationship(
        "Location",
        back_populates="purchase_orders",
    )
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="purchase_orders",
    )
    grn_records: Mapped[list["GRNRecord"]] = relationship(
        "GRNRecord",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number})>"

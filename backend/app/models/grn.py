"""GRN (Goods Receipt Note) Record model."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GRNRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """GRN Record model for tracking goods receipts."""
    
    __tablename__ = "grn_records"
    
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grn_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="grn_records",
    )
    
    def __repr__(self) -> str:
        return f"<GRNRecord(id={self.id}, po_id={self.po_id}, grn_date={self.grn_date})>"

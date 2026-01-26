"""Location model."""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LocationType(str, enum.Enum):
    """Location type enumeration."""
    
    STORE = "store"
    WAREHOUSE = "warehouse"


class Location(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Location model representing stores and warehouses."""
    
    __tablename__ = "locations"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[LocationType] = mapped_column(
        Enum(LocationType, name="location_type", create_type=True),
        nullable=False,
    )
    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clusters.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    cluster: Mapped["Cluster"] = relationship(
        "Cluster",
        back_populates="locations",
    )
    season_plans: Mapped[list["SeasonPlan"]] = relationship(
        "SeasonPlan",
        back_populates="location",
    )
    otb_plans: Mapped[list["OTBPlan"]] = relationship(
        "OTBPlan",
        back_populates="location",
    )
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="location",
    )
    
    def __repr__(self) -> str:
        return f"<Location(id={self.id}, name={self.name}, type={self.type})>"

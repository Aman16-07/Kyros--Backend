"""Season model."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SeasonStatus(str, enum.Enum):
    """Season workflow status enumeration."""
    
    CREATED = "created"
    LOCATIONS_DEFINED = "locations_defined"
    PLAN_UPLOADED = "plan_uploaded"
    OTB_UPLOADED = "otb_uploaded"
    RANGE_UPLOADED = "range_uploaded"
    LOCKED = "locked"


class Season(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Season model representing business planning seasons."""
    
    __tablename__ = "seasons"
    
    # Custom readable ID in format XXXX-XXXX (e.g., F9J1-KKG2)
    season_code: Mapped[str] = mapped_column(
        String(9), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[SeasonStatus] = mapped_column(
        Enum(SeasonStatus, name="season_status", create_type=True),
        nullable=False,
        default=SeasonStatus.CREATED,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_seasons",
        foreign_keys=[created_by],
    )
    season_plans: Mapped[list["SeasonPlan"]] = relationship(
        "SeasonPlan",
        back_populates="season",
        cascade="all, delete-orphan",
    )
    otb_plans: Mapped[list["OTBPlan"]] = relationship(
        "OTBPlan",
        back_populates="season",
        cascade="all, delete-orphan",
    )
    range_intents: Mapped[list["RangeIntent"]] = relationship(
        "RangeIntent",
        back_populates="season",
        cascade="all, delete-orphan",
    )
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="season",
        cascade="all, delete-orphan",
    )
    workflow: Mapped["SeasonWorkflow"] = relationship(
        "SeasonWorkflow",
        back_populates="season",
        uselist=False,
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Season(id={self.id}, name={self.name}, status={self.status})>"

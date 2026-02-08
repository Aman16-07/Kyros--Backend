"""Company model for multi-tenant organization management."""

import enum
import random
import string
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class CompanyStatus(str, enum.Enum):
    """Company registration status."""
    
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


def generate_company_code() -> str:
    """Generate a unique 8-digit alphanumeric company code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Company model for multi-tenant organization management."""
    
    __tablename__ = "companies"
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(
        String(9),  # Format: XXXX-XXXX
        unique=True, 
        nullable=True,  # Nullable until approved
        index=True,
    )
    
    # Company details
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status and approval workflow
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, name="company_status", create_type=True, 
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=CompanyStatus.PENDING,
    )
    
    # Request notes from the requester
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Approval tracking
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    # Rejection tracking
    rejected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Updated timestamp
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="company",
        foreign_keys="User.company_id",
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by],
    )
    seasons: Mapped[list["Season"]] = relationship(
        "Season",
        back_populates="company",
        foreign_keys="Season.company_id",
    )
    clusters: Mapped[list["Cluster"]] = relationship(
        "Cluster",
        back_populates="company",
        foreign_keys="Cluster.company_id",
    )
    locations: Mapped[list["Location"]] = relationship(
        "Location",
        back_populates="company",
        foreign_keys="Location.company_id",
    )
    
    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, code={self.code}, status={self.status})>"

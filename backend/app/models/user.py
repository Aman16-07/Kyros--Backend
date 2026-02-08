"""User model."""

import enum
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company


class UserRole(str, enum.Enum):
    """User role enumeration."""
    
    SUPER_ADMIN = "super_admin"  # System administrator (Kyros staff)
    ADMIN = "admin"              # Company administrator
    MANAGER = "manager"          # Company manager
    VIEWER = "viewer"            # Read-only user


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User model representing system users."""
    
    __tablename__ = "users"
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Role and status
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_type=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=UserRole.VIEWER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Organization (multi-tenant) - link to company
    company_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Auth tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Updated timestamp
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    
    # Relationships
    company: Mapped[Optional["Company"]] = relationship(
        "Company",
        back_populates="users",
        foreign_keys=[company_id],
    )
    created_seasons: Mapped[list["Season"]] = relationship(
        "Season",
        back_populates="creator",
        foreign_keys="Season.created_by",
    )
    uploaded_season_plans: Mapped[list["SeasonPlan"]] = relationship(
        "SeasonPlan",
        back_populates="uploader",
        foreign_keys="SeasonPlan.uploaded_by",
    )
    uploaded_otb_plans: Mapped[list["OTBPlan"]] = relationship(
        "OTBPlan",
        back_populates="uploader",
        foreign_keys="OTBPlan.uploaded_by",
    )
    uploaded_range_intents: Mapped[list["RangeIntent"]] = relationship(
        "RangeIntent",
        back_populates="uploader",
        foreign_keys="RangeIntent.uploaded_by",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        foreign_keys="AuditLog.user_id",
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        foreign_keys="UserSession.user_id",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"

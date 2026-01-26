"""User model."""

import enum
import uuid

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    """User role enumeration."""
    
    ADMIN = "admin"
    VIEWER = "viewer"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User model representing system users."""
    
    __tablename__ = "users"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_type=True),
        nullable=False,
        default=UserRole.VIEWER,
    )
    
    # Relationships
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
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"

"""Audit Log model for tracking all system changes."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class AuditAction(str, Enum):
    """Types of audit actions."""
    
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    LOCK = "lock"
    UNLOCK = "unlock"
    LOGIN = "login"
    LOGOUT = "logout"
    UPLOAD = "upload"
    WORKFLOW_TRANSITION = "workflow_transition"


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """
    Audit Log model for tracking all data changes.
    
    Captures who changed what, when, and the before/after values.
    """
    
    __tablename__ = "audit_logs"
    
    # What entity was affected
    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # What action was performed
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, name="audit_action", create_type=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    
    # Who performed the action
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # When the action was performed
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    
    # Before and after state (for updates)
    old_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    new_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Additional context
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # IP address and user agent for security auditing
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    # Season context (for easy filtering)
    season_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seasons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[user_id],
    )
    season: Mapped[Optional["Season"]] = relationship(
        "Season",
        foreign_keys=[season_id],
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, entity_type={self.entity_type}, action={self.action})>"

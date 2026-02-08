"""Cluster model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Cluster(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cluster model representing location groups."""
    
    __tablename__ = "clusters"
    
    # Auto-generated unique cluster code (e.g., CLU-A7B3C9D1)
    cluster_code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Multi-tenant isolation
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Relationships
    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="clusters",
        foreign_keys=[company_id],
    )
    locations: Mapped[list["Location"]] = relationship(
        "Location",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Cluster(id={self.id}, code={self.cluster_code}, name={self.name})>"

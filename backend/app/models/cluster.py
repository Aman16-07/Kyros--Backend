"""Cluster model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Cluster(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cluster model representing location groups."""
    
    __tablename__ = "clusters"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    # Relationships
    locations: Mapped[list["Location"]] = relationship(
        "Location",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Cluster(id={self.id}, name={self.name})>"

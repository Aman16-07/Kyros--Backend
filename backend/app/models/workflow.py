"""Season Workflow model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SeasonWorkflow(Base):
    """Season Workflow model for tracking season progression."""
    
    __tablename__ = "season_workflow"
    
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seasons.id", ondelete="CASCADE"),
        primary_key=True,
    )
    locations_defined: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    plan_uploaded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    otb_uploaded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    range_uploaded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    locked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    season: Mapped["Season"] = relationship(
        "Season",
        back_populates="workflow",
    )
    
    def __repr__(self) -> str:
        return f"<SeasonWorkflow(season_id={self.season_id}, locked={self.locked})>"

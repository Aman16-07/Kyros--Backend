"""Season schemas."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.season import SeasonStatus
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class SeasonBase(BaseSchema):
    """Base season schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    
    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: date, info) -> date:
        """Ensure end_date is after start_date."""
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class SeasonCreate(SeasonBase):
    """Schema for creating a season."""
    
    created_by: Optional[UUID] = None
    # season_code will be auto-generated


class SeasonUpdate(BaseSchema):
    """Schema for updating a season."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    # status cannot be directly updated - must use workflow transitions


class SeasonResponse(SeasonBase, UUIDSchema, TimestampSchema):
    """Schema for season response."""
    
    season_code: str = Field(..., description="Unique season code in format XXXX-XXXX")
    status: SeasonStatus
    created_by: Optional[UUID] = None


class SeasonWithWorkflow(SeasonResponse):
    """Schema for season with workflow status."""
    
    workflow: Optional["WorkflowResponse"] = None


class WorkflowResponse(BaseSchema):
    """Schema for workflow status."""
    
    season_id: UUID
    locations_defined: bool
    plan_uploaded: bool
    otb_uploaded: bool
    range_uploaded: bool
    locked: bool
    updated_at: datetime


class SeasonListResponse(BaseSchema):
    """Schema for list of seasons."""
    
    items: list[SeasonResponse]
    total: int


# Update forward reference
SeasonWithWorkflow.model_rebuild()

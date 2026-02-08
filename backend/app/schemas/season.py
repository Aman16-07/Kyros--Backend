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
    company_id: Optional[UUID] = None
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
    
    @property
    def is_editable(self) -> bool:
        """Check if the season is still editable (not locked)."""
        return not self.locked
    
    @property
    def current_step(self) -> str:
        """Get the current workflow step name."""
        if self.locked:
            return "locked"
        if self.range_uploaded:
            return "range_uploaded"
        if self.otb_uploaded:
            return "otb_uploaded"
        if self.plan_uploaded:
            return "plan_uploaded"
        if self.locations_defined:
            return "locations_defined"
        return "created"
    
    @property
    def next_step(self) -> Optional[str]:
        """Get the next step in the workflow."""
        if self.locked:
            return None  # No next step after locked
        if self.range_uploaded:
            return "lock"
        if self.otb_uploaded:
            return "upload_range_intent"
        if self.plan_uploaded:
            return "upload_otb"
        if self.locations_defined:
            return "upload_plan"
        return "define_locations"


class WorkflowStatusResponse(WorkflowResponse):
    """Extended workflow status with computed fields."""
    
    is_editable: bool = Field(True, description="Whether season data can still be edited")
    current_step: str = Field("created", description="Current workflow step")
    next_step: Optional[str] = Field(None, description="Next step in workflow")
    can_edit_plans: bool = Field(True, description="Whether season plans can be edited")
    can_edit_otb: bool = Field(True, description="Whether OTB plans can be edited")
    can_edit_range: bool = Field(True, description="Whether range intents can be edited")
    can_add_po: bool = Field(False, description="Whether POs can be added")
    can_add_grn: bool = Field(False, description="Whether GRNs can be added")
    
    @classmethod
    def from_workflow(cls, workflow: "WorkflowResponse") -> "WorkflowStatusResponse":
        """Create extended status from basic workflow response."""
        # Calculate current step
        if workflow.locked:
            current_step = "locked"
        elif workflow.range_uploaded:
            current_step = "range_uploaded"
        elif workflow.otb_uploaded:
            current_step = "otb_uploaded"
        elif workflow.plan_uploaded:
            current_step = "plan_uploaded"
        elif workflow.locations_defined:
            current_step = "locations_defined"
        else:
            current_step = "created"
        
        # Calculate next step
        if workflow.locked:
            next_step = None
        elif workflow.range_uploaded:
            next_step = "lock"
        elif workflow.otb_uploaded:
            next_step = "upload_range_intent"
        elif workflow.plan_uploaded:
            next_step = "upload_otb"
        elif workflow.locations_defined:
            next_step = "upload_plan"
        else:
            next_step = "define_locations"
        
        return cls(
            season_id=workflow.season_id,
            locations_defined=workflow.locations_defined,
            plan_uploaded=workflow.plan_uploaded,
            otb_uploaded=workflow.otb_uploaded,
            range_uploaded=workflow.range_uploaded,
            locked=workflow.locked,
            updated_at=workflow.updated_at,
            is_editable=not workflow.locked,
            current_step=current_step,
            next_step=next_step,
            # Once locked, no edits allowed
            can_edit_plans=not workflow.locked,
            can_edit_otb=not workflow.locked,
            can_edit_range=not workflow.locked,
            # Can add PO/GRN only after locked
            can_add_po=workflow.locked,
            can_add_grn=workflow.locked,
        )


class SeasonListResponse(BaseSchema):
    """Schema for list of seasons."""
    
    items: list[SeasonResponse]
    total: int


# Update forward reference
SeasonWithWorkflow.model_rebuild()

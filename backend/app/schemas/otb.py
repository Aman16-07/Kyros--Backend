"""OTB Plan schemas."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class OTBPlanBase(BaseSchema):
    """Base OTB plan schema."""
    
    season_id: UUID
    location_id: UUID
    category_id: UUID
    month: date
    approved_spend_limit: Decimal = Field(..., ge=0, decimal_places=2)
    
    @field_validator("approved_spend_limit", mode="before")
    @classmethod
    def round_decimal(cls, v):
        """Round decimal to 2 places."""
        if v is not None:
            return round(Decimal(str(v)), 2)
        return v
    
    @field_validator("month")
    @classmethod
    def validate_month(cls, v: date) -> date:
        """Ensure month is first day of month."""
        return v.replace(day=1)


class OTBPlanCreate(OTBPlanBase):
    """Schema for creating an OTB plan."""
    
    uploaded_by: Optional[UUID] = None


class OTBPlanUpdate(BaseSchema):
    """Schema for updating an OTB plan."""
    
    approved_spend_limit: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class OTBPlanResponse(OTBPlanBase, UUIDSchema, TimestampSchema):
    """Schema for OTB plan response."""
    
    uploaded_by: Optional[UUID] = None


class OTBPlanWithDetails(OTBPlanResponse):
    """Schema for OTB plan with related entity names."""
    
    season_name: Optional[str] = None
    location_name: Optional[str] = None
    category_name: Optional[str] = None


class OTBPlanListResponse(BaseSchema):
    """Schema for list of OTB plans."""
    
    items: list[OTBPlanResponse]
    total: int


class OTBPlanBulkCreate(BaseSchema):
    """Schema for bulk creating OTB plans."""
    
    plans: list[OTBPlanCreate]


class OTBSummary(BaseSchema):
    """Schema for OTB summary by month."""
    
    month: date
    total_spend_limit: Decimal
    location_count: int
    category_count: int

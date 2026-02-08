"""Season Plan schemas."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class SeasonPlanBase(BaseSchema):
    """Base season plan schema."""
    
    season_id: UUID
    location_id: UUID
    category_id: UUID
    sku_id: Optional[str] = Field(None, max_length=100, description="SKU identifier")
    planned_sales: Decimal = Field(..., ge=0, decimal_places=2)
    planned_margin: Decimal = Field(..., decimal_places=2)
    planned_units: Optional[int] = Field(None, ge=0, description="Planned unit quantity")
    inventory_turns: Decimal = Field(..., ge=0, decimal_places=2)
    ly_sales: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Last year sales")
    lly_sales: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Last last year sales")
    
    @field_validator("planned_sales", "planned_margin", "inventory_turns", "ly_sales", "lly_sales", mode="before")
    @classmethod
    def round_decimal(cls, v):
        """Round decimal to 2 places."""
        if v is not None:
            return round(Decimal(str(v)), 2)
        return v


class SeasonPlanCreate(SeasonPlanBase):
    """Schema for creating a season plan."""
    
    version: int = Field(default=1, ge=1)
    uploaded_by: Optional[UUID] = None
    approved: bool = False


class SeasonPlanUpdate(BaseSchema):
    """Schema for updating a season plan."""
    
    planned_sales: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    planned_margin: Optional[Decimal] = Field(None, decimal_places=2)
    planned_units: Optional[int] = Field(None, ge=0)
    inventory_turns: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    ly_sales: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    lly_sales: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    approved: Optional[bool] = None


class SeasonPlanResponse(SeasonPlanBase, UUIDSchema, TimestampSchema):
    """Schema for season plan response."""
    
    version: int
    uploaded_by: Optional[UUID] = None
    approved: bool


class SeasonPlanWithDetails(SeasonPlanResponse):
    """Schema for season plan with related entity names."""
    
    season_name: Optional[str] = None
    location_name: Optional[str] = None
    category_name: Optional[str] = None


class SeasonPlanListResponse(BaseSchema):
    """Schema for list of season plans."""
    
    items: list[SeasonPlanResponse]
    total: int


class SeasonPlanBulkCreate(BaseSchema):
    """Schema for bulk creating season plans."""
    
    plans: list[SeasonPlanCreate]


class SeasonPlanApproveRequest(BaseSchema):
    """Schema for approving season plans."""
    
    plan_ids: list[UUID]
    approved: bool = True

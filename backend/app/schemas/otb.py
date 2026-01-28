"""OTB Plan schemas.

OTB Formula: Planned Sales + Planned Closing Stock - Opening Stock - On Order
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class OTBPlanBase(BaseSchema):
    """Base OTB plan schema."""
    
    season_id: UUID
    location_id: UUID
    category_id: UUID
    month: date
    
    # OTB Formula Components
    planned_sales: Decimal = Field(..., ge=0, decimal_places=2, description="Planned sales value")
    planned_closing_stock: Decimal = Field(..., ge=0, decimal_places=2, description="Planned closing stock")
    opening_stock: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, description="Opening stock")
    on_order: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, description="On order value")
    
    @field_validator("planned_sales", "planned_closing_stock", "opening_stock", "on_order", mode="before")
    @classmethod
    def round_decimal(cls, v):
        """Round decimal to 2 places."""
        if v is not None:
            return round(Decimal(str(v)), 2)
        return Decimal("0.00")
    
    @field_validator("month")
    @classmethod
    def validate_month(cls, v: date) -> date:
        """Ensure month is first day of month."""
        return v.replace(day=1)


class OTBPlanCreate(OTBPlanBase):
    """Schema for creating an OTB plan."""
    
    uploaded_by: Optional[UUID] = None
    # approved_spend_limit is calculated automatically from formula


class OTBPlanUpdate(BaseSchema):
    """Schema for updating an OTB plan."""
    
    planned_sales: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    planned_closing_stock: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    opening_stock: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    on_order: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class OTBPlanResponse(OTBPlanBase, UUIDSchema, TimestampSchema):
    """Schema for OTB plan response."""
    
    approved_spend_limit: Decimal = Field(..., description="Calculated OTB value")
    uploaded_by: Optional[UUID] = None
    
    @property
    def otb_breakdown(self) -> dict:
        """Return OTB calculation breakdown."""
        return {
            "planned_sales": self.planned_sales,
            "planned_closing_stock": self.planned_closing_stock,
            "opening_stock": self.opening_stock,
            "on_order": self.on_order,
            "calculated_otb": self.approved_spend_limit,
            "formula": "Planned Sales + Planned Closing Stock - Opening Stock - On Order"
        }


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

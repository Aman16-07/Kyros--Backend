"""Purchase Order schemas."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.purchase_order import POSource
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class PurchaseOrderBase(BaseSchema):
    """Base purchase order schema."""
    
    po_number: str = Field(..., min_length=1, max_length=100)
    season_id: UUID
    location_id: UUID
    category_id: UUID
    po_value: Decimal = Field(..., ge=0, decimal_places=2)
    source: POSource
    
    @field_validator("po_value", mode="before")
    @classmethod
    def round_decimal(cls, v):
        """Round decimal to 2 places."""
        if v is not None:
            return round(Decimal(str(v)), 2)
        return v


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""
    
    pass


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a purchase order."""
    
    po_value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class PurchaseOrderResponse(PurchaseOrderBase, UUIDSchema, TimestampSchema):
    """Schema for purchase order response."""
    
    pass


class PurchaseOrderWithDetails(PurchaseOrderResponse):
    """Schema for purchase order with related entity names."""
    
    season_name: Optional[str] = None
    location_name: Optional[str] = None
    category_name: Optional[str] = None
    total_received: Optional[Decimal] = None


class PurchaseOrderListResponse(BaseSchema):
    """Schema for list of purchase orders."""
    
    items: list[PurchaseOrderResponse]
    total: int


class PurchaseOrderBulkCreate(BaseSchema):
    """Schema for bulk creating purchase orders via CSV."""
    
    orders: list[PurchaseOrderCreate]


class POSummary(BaseSchema):
    """Schema for PO summary."""
    
    total_orders: int
    total_value: Decimal
    by_source: dict[str, int]

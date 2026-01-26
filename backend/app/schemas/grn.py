"""GRN Record schemas."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class GRNRecordBase(BaseSchema):
    """Base GRN record schema."""
    
    po_id: UUID
    grn_date: date
    received_value: Decimal = Field(..., ge=0, decimal_places=2)
    
    @field_validator("received_value", mode="before")
    @classmethod
    def round_decimal(cls, v):
        """Round decimal to 2 places."""
        if v is not None:
            return round(Decimal(str(v)), 2)
        return v


class GRNRecordCreate(GRNRecordBase):
    """Schema for creating a GRN record."""
    
    pass


class GRNRecordUpdate(BaseSchema):
    """Schema for updating a GRN record."""
    
    grn_date: Optional[date] = None
    received_value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class GRNRecordResponse(GRNRecordBase, UUIDSchema, TimestampSchema):
    """Schema for GRN record response."""
    
    pass


class GRNRecordWithPO(GRNRecordResponse):
    """Schema for GRN record with PO details."""
    
    po_number: Optional[str] = None
    po_value: Optional[Decimal] = None


class GRNRecordListResponse(BaseSchema):
    """Schema for list of GRN records."""
    
    items: list[GRNRecordResponse]
    total: int


class GRNRecordBulkCreate(BaseSchema):
    """Schema for bulk creating GRN records via CSV."""
    
    records: list[GRNRecordCreate]


class GRNSummary(BaseSchema):
    """Schema for GRN summary."""
    
    total_records: int
    total_received_value: Decimal
    by_month: dict[str, Decimal]

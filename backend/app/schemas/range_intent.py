"""Range Intent schemas."""

from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class RangeIntentBase(BaseSchema):
    """Base range intent schema."""
    
    season_id: UUID
    category_id: UUID
    core_percent: Decimal = Field(..., ge=0, le=100, decimal_places=2)
    fashion_percent: Decimal = Field(..., ge=0, le=100, decimal_places=2)
    price_band_mix: dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode="after")
    def validate_percentages(self):
        """Ensure core + fashion = 100."""
        total = self.core_percent + self.fashion_percent
        if total != Decimal("100.00"):
            raise ValueError(f"core_percent + fashion_percent must equal 100, got {total}")
        return self


class RangeIntentCreate(RangeIntentBase):
    """Schema for creating a range intent."""
    
    uploaded_by: Optional[UUID] = None


class RangeIntentUpdate(BaseSchema):
    """Schema for updating a range intent."""
    
    core_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    fashion_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    price_band_mix: Optional[dict[str, Any]] = None


class RangeIntentResponse(RangeIntentBase, UUIDSchema, TimestampSchema):
    """Schema for range intent response."""
    
    uploaded_by: Optional[UUID] = None


class RangeIntentWithDetails(RangeIntentResponse):
    """Schema for range intent with related entity names."""
    
    season_name: Optional[str] = None
    category_name: Optional[str] = None


class RangeIntentListResponse(BaseSchema):
    """Schema for list of range intents."""
    
    items: list[RangeIntentResponse]
    total: int


class RangeIntentBulkCreate(BaseSchema):
    """Schema for bulk creating range intents."""
    
    intents: list[RangeIntentCreate]

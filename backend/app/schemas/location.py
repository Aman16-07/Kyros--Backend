"""Location schemas."""

from typing import Optional
from uuid import UUID

from pydantic import Field

from app.models.location import LocationType
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class LocationBase(BaseSchema):
    """Base location schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    type: LocationType


class LocationCreate(LocationBase):
    """Schema for creating a location."""
    
    cluster_id: Optional[UUID] = None
    # location_code will be auto-generated (16-character unique ID)
    
    # Address fields
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Activation status
    is_active: bool = True


class LocationUpdate(BaseSchema):
    """Schema for updating a location."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[LocationType] = None
    cluster_id: Optional[UUID] = None
    
    # Address fields
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Activation status
    is_active: Optional[bool] = None


class LocationResponse(LocationBase, UUIDSchema, TimestampSchema):
    """Schema for location response."""
    
    location_code: str = Field(..., description="Unique 16-character location code")
    cluster_id: Optional[UUID] = None
    
    # Address fields
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Activation status
    is_active: bool = True


class LocationWithCluster(LocationResponse):
    """Schema for location with cluster details."""
    
    cluster_name: Optional[str] = None


class LocationListResponse(BaseSchema):
    """Schema for list of locations."""
    
    items: list[LocationResponse]
    total: int


class LocationBulkCreate(BaseSchema):
    """Schema for bulk creating locations."""
    
    locations: list[LocationCreate]

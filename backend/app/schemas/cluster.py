"""Cluster schemas."""

from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class ClusterBase(BaseSchema):
    """Base cluster schema."""
    
    name: str = Field(..., min_length=1, max_length=255)


class ClusterCreate(ClusterBase):
    """Schema for creating a cluster."""
    
    pass


class ClusterUpdate(BaseSchema):
    """Schema for updating a cluster."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class ClusterResponse(ClusterBase, UUIDSchema, TimestampSchema):
    """Schema for cluster response."""
    
    pass


class ClusterWithLocations(ClusterResponse):
    """Schema for cluster with locations."""
    
    locations: list["LocationResponse"] = []


class ClusterListResponse(BaseSchema):
    """Schema for list of clusters."""
    
    items: list[ClusterResponse]
    total: int


# Import here to avoid circular imports
from app.schemas.location import LocationResponse

ClusterWithLocations.model_rebuild()

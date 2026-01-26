"""Locations API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession
from app.models.location import LocationType
from app.repositories.location_repo import LocationRepository
from app.schemas.location import (
    LocationBulkCreate,
    LocationCreate,
    LocationListResponse,
    LocationResponse,
    LocationUpdate,
)

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new location",
)
async def create_location(
    data: LocationCreate,
    db: DBSession,
) -> LocationResponse:
    """Create a new location."""
    repo = LocationRepository(db)
    
    location = await repo.create(
        name=data.name,
        type=data.type,
        cluster_id=data.cluster_id,
    )
    return LocationResponse.model_validate(location)


@router.post(
    "/bulk",
    response_model=LocationListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create locations",
)
async def bulk_create_locations(
    data: LocationBulkCreate,
    db: DBSession,
) -> LocationListResponse:
    """Bulk create locations."""
    repo = LocationRepository(db)
    
    locations = await repo.bulk_create([
        {"name": loc.name, "type": loc.type, "cluster_id": loc.cluster_id}
        for loc in data.locations
    ])
    
    return LocationListResponse(
        items=[LocationResponse.model_validate(loc) for loc in locations],
        total=len(locations),
    )


@router.get(
    "",
    response_model=LocationListResponse,
    summary="Get all locations",
)
async def get_locations(
    db: DBSession,
    location_type: Optional[LocationType] = Query(None, alias="type", description="Filter by type"),
    cluster_id: Optional[UUID] = Query(None, description="Filter by cluster"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> LocationListResponse:
    """Get all locations with optional filtering."""
    repo = LocationRepository(db)
    
    if location_type:
        locations = await repo.get_by_type(location_type, skip, limit)
        total = await repo.count(type=location_type)
    elif cluster_id:
        locations = await repo.get_by_cluster(cluster_id, skip, limit)
        total = await repo.count(cluster_id=cluster_id)
    else:
        locations = await repo.get_all(skip, limit)
        total = await repo.count()
    
    return LocationListResponse(
        items=[LocationResponse.model_validate(loc) for loc in locations],
        total=total,
    )


@router.get(
    "/stores",
    response_model=LocationListResponse,
    summary="Get all store locations",
)
async def get_stores(
    db: DBSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> LocationListResponse:
    """Get all store locations."""
    repo = LocationRepository(db)
    locations = await repo.get_stores(skip, limit)
    total = await repo.count(type=LocationType.STORE)
    
    return LocationListResponse(
        items=[LocationResponse.model_validate(loc) for loc in locations],
        total=total,
    )


@router.get(
    "/warehouses",
    response_model=LocationListResponse,
    summary="Get all warehouse locations",
)
async def get_warehouses(
    db: DBSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> LocationListResponse:
    """Get all warehouse locations."""
    repo = LocationRepository(db)
    locations = await repo.get_warehouses(skip, limit)
    total = await repo.count(type=LocationType.WAREHOUSE)
    
    return LocationListResponse(
        items=[LocationResponse.model_validate(loc) for loc in locations],
        total=total,
    )


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Get a location by ID",
)
async def get_location(
    location_id: UUID,
    db: DBSession,
) -> LocationResponse:
    """Get a location by ID."""
    repo = LocationRepository(db)
    location = await repo.get_by_id(location_id)
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    return LocationResponse.model_validate(location)


@router.patch(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Update a location",
)
async def update_location(
    location_id: UUID,
    data: LocationUpdate,
    db: DBSession,
) -> LocationResponse:
    """Update a location."""
    repo = LocationRepository(db)
    
    update_data = data.model_dump(exclude_unset=True)
    location = await repo.update(location_id, **update_data)
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    return LocationResponse.model_validate(location)


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a location",
)
async def delete_location(
    location_id: UUID,
    db: DBSession,
) -> None:
    """Delete a location."""
    repo = LocationRepository(db)
    deleted = await repo.delete(location_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

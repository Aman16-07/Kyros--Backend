"""Locations API endpoints.

Locations are defined as part of the workflow Step 2.
Each location gets an auto-generated 16-character unique location_code.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.core.deps import DBSession, get_current_user
from app.models.location import Location, LocationType
from app.models.user import User
from app.repositories.location_repo import LocationRepository
from app.schemas.location import (
    LocationBulkCreate,
    LocationCreate,
    LocationListResponse,
    LocationResponse,
    LocationUpdate,
)
from app.services.audit_service import AuditService
from app.utils.id_generators import generate_location_id

router = APIRouter(prefix="/locations", tags=["Locations"])


async def _get_existing_location_codes(db) -> set[str]:
    """Get all existing location codes."""
    result = await db.execute(select(Location.location_code))
    return {row[0] for row in result.all() if row[0]}


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new location",
    description="""
    Create a new location with auto-generated location_code.
    
    Location code: 16-character unique alphanumeric (e.g., A7B3C9D1E5F2G8H4)
    
    This is part of Step 2 (Define Locations) in the workflow.
    """,
)
async def create_location(
    data: LocationCreate,
    db: DBSession,
    current_user: User = Depends(get_current_user),
) -> LocationResponse:
    """Create a new location with auto-generated location_code."""
    repo = LocationRepository(db)
    audit = AuditService(db)
    
    # Generate unique location code
    existing_codes = await _get_existing_location_codes(db)
    location_code = generate_location_id(existing_codes)
    
    location = await repo.create(
        location_code=location_code,
        name=data.name,
        type=data.type,
        cluster_id=data.cluster_id,
        company_id=current_user.company_id,
        address=data.address,
        city=data.city,
        state=data.state,
        country=data.country,
        postal_code=data.postal_code,
        is_active=data.is_active,
    )
    
    # Audit log the creation
    await audit.log_create(
        entity_type="Location",
        entity_id=location.id,
        user_id=current_user.id,
        new_data={
            "name": data.name,
            "location_code": location_code,
            "type": str(data.type) if data.type else None,
            "cluster_id": str(data.cluster_id) if data.cluster_id else None,
            "city": data.city,
            "is_active": data.is_active,
        },
    )
    
    return LocationResponse.model_validate(location)


@router.post(
    "/bulk",
    response_model=LocationListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create locations",
    description="""
    Bulk create locations with auto-generated location_codes.
    
    Each location gets a unique 16-character alphanumeric code.
    This is useful for defining multiple stores/warehouses at once.
    """,
)
async def bulk_create_locations(
    data: LocationBulkCreate,
    db: DBSession,
    current_user: User = Depends(get_current_user),
) -> LocationListResponse:
    """Bulk create locations with auto-generated location_codes."""
    repo = LocationRepository(db)
    audit = AuditService(db)
    
    # Generate unique codes for all locations
    existing_codes = await _get_existing_location_codes(db)
    
    locations = []
    for loc in data.locations:
        location_code = generate_location_id(existing_codes)
        existing_codes.add(location_code)  # Avoid duplicates in same batch
        
        location = await repo.create(
            location_code=location_code,
            name=loc.name,
            type=loc.type,
            cluster_id=loc.cluster_id,
            company_id=current_user.company_id,
            address=loc.address,
            city=loc.city,
            state=loc.state,
            country=loc.country,
            postal_code=loc.postal_code,
            is_active=loc.is_active,
        )
        locations.append(location)
        
        # Audit log each creation
        await audit.log_create(
            entity_type="Location",
            entity_id=location.id,
            user_id=current_user.id,
            new_data={
                "name": loc.name,
                "location_code": location_code,
                "type": str(loc.type) if loc.type else None,
                "cluster_id": str(loc.cluster_id) if loc.cluster_id else None,
            },
        )
    
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
    current_user: User = Depends(get_current_user),
    location_type: Optional[LocationType] = Query(None, alias="type", description="Filter by type"),
    cluster_id: Optional[UUID] = Query(None, description="Filter by cluster"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> LocationListResponse:
    """Get all locations for the current user's company with optional filtering."""
    repo = LocationRepository(db)
    
    # Get locations filtered by company
    locations = await repo.get_by_company(
        company_id=current_user.company_id,
        location_type=location_type,
        cluster_id=cluster_id,
        skip=skip,
        limit=limit,
    )
    total = await repo.count_by_company(
        company_id=current_user.company_id,
        location_type=location_type,
        cluster_id=cluster_id,
    )
    
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
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> LocationListResponse:
    """Get all store locations for the current user's company."""
    repo = LocationRepository(db)
    locations = await repo.get_by_company(
        company_id=current_user.company_id,
        location_type=LocationType.STORE,
        skip=skip,
        limit=limit,
    )
    total = await repo.count_by_company(
        company_id=current_user.company_id,
        location_type=LocationType.STORE,
    )
    
    return LocationListResponse(
        items=[LocationResponse.model_validate(loc) for loc in locations],
        total=total,
    )


@router.get(
    "/lookup",
    response_model=dict,
    summary="Lookup locations by name",
    description="Get a mapping of location names to their UUIDs. Useful for CSV uploads.",
)
async def lookup_locations_by_name(
    db: DBSession,
    current_user: User = Depends(get_current_user),
    names: list[str] = Query(..., description="List of location names to lookup"),
) -> dict:
    """Lookup location IDs by name within current user's company."""
    repo = LocationRepository(db)
    result = {}
    for name in names:
        location = await repo.get_by_name_and_company(name, current_user.company_id)
        if location:
            result[name] = str(location.id)
        else:
            result[name] = None
    return result


@router.get(
    "/warehouses",
    response_model=LocationListResponse,
    summary="Get all warehouse locations",
)
async def get_warehouses(
    db: DBSession,
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> LocationListResponse:
    """Get all warehouse locations for the current user's company."""
    repo = LocationRepository(db)
    locations = await repo.get_by_company(
        company_id=current_user.company_id,
        location_type=LocationType.WAREHOUSE,
        skip=skip,
        limit=limit,
    )
    total = await repo.count_by_company(
        company_id=current_user.company_id,
        location_type=LocationType.WAREHOUSE,
    )
    
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
    current_user: User = Depends(get_current_user),
) -> LocationResponse:
    """Get a location by ID."""
    repo = LocationRepository(db)
    location = await repo.get_by_id(location_id)
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    # Verify location belongs to user's company
    if location.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this location",
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
    current_user: User = Depends(get_current_user),
) -> LocationResponse:
    """Update a location."""
    repo = LocationRepository(db)
    audit = AuditService(db)
    
    # Verify location exists and belongs to user's company
    existing = await repo.get_by_id(location_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    if existing.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this location",
        )
    
    # Capture old data for audit
    old_data = {
        "name": existing.name,
        "type": existing.type.value if existing.type else None,
        "city": existing.city,
        "is_active": existing.is_active,
    }
    
    update_data = data.model_dump(exclude_unset=True)
    location = await repo.update(location_id, **update_data)
    
    # Audit log the update
    await audit.log_update(
        entity_type="Location",
        entity_id=location_id,
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data,
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
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a location."""
    repo = LocationRepository(db)
    audit = AuditService(db)
    
    # Verify location exists and belongs to user's company
    existing = await repo.get_by_id(location_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    if existing.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this location",
        )
    
    # Capture old data for audit
    old_data = {
        "id": str(existing.id),
        "name": existing.name,
        "location_code": existing.location_code,
        "type": existing.type.value if existing.type else None,
    }
    
    await repo.delete(location_id)
    
    # Audit log the deletion
    await audit.log_delete(
        entity_type="Location",
        entity_id=location_id,
        user_id=current_user.id,
        old_data=old_data,
    )

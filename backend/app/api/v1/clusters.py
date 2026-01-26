"""Clusters API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession
from app.repositories.cluster_repo import ClusterRepository
from app.schemas.cluster import (
    ClusterCreate,
    ClusterListResponse,
    ClusterResponse,
    ClusterUpdate,
    ClusterWithLocations,
)

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.post(
    "",
    response_model=ClusterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cluster",
)
async def create_cluster(
    data: ClusterCreate,
    db: DBSession,
) -> ClusterResponse:
    """Create a new cluster."""
    repo = ClusterRepository(db)
    
    # Check for duplicate name
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cluster with this name already exists",
        )
    
    cluster = await repo.create(name=data.name)
    return ClusterResponse.model_validate(cluster)


@router.get(
    "",
    response_model=ClusterListResponse,
    summary="Get all clusters",
)
async def get_clusters(
    db: DBSession,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> ClusterListResponse:
    """Get all clusters."""
    repo = ClusterRepository(db)
    clusters = await repo.get_all(skip, limit)
    total = await repo.count()
    
    return ClusterListResponse(
        items=[ClusterResponse.model_validate(c) for c in clusters],
        total=total,
    )


@router.get(
    "/{cluster_id}",
    response_model=ClusterWithLocations,
    summary="Get a cluster by ID",
)
async def get_cluster(
    cluster_id: UUID,
    db: DBSession,
) -> ClusterWithLocations:
    """Get a cluster by ID with its locations."""
    repo = ClusterRepository(db)
    cluster = await repo.get_with_locations(cluster_id)
    
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )
    
    return ClusterWithLocations.model_validate(cluster)


@router.patch(
    "/{cluster_id}",
    response_model=ClusterResponse,
    summary="Update a cluster",
)
async def update_cluster(
    cluster_id: UUID,
    data: ClusterUpdate,
    db: DBSession,
) -> ClusterResponse:
    """Update a cluster."""
    repo = ClusterRepository(db)
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Check for duplicate name if updating name
    if "name" in update_data:
        existing = await repo.get_by_name(update_data["name"])
        if existing and existing.id != cluster_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cluster with this name already exists",
            )
    
    cluster = await repo.update(cluster_id, **update_data)
    
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )
    
    return ClusterResponse.model_validate(cluster)


@router.delete(
    "/{cluster_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cluster",
)
async def delete_cluster(
    cluster_id: UUID,
    db: DBSession,
) -> None:
    """Delete a cluster."""
    repo = ClusterRepository(db)
    deleted = await repo.delete(cluster_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

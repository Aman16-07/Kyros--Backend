"""Clusters API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession, get_current_user
from app.models.user import User
from app.repositories.cluster_repo import ClusterRepository, generate_cluster_code
from app.schemas.cluster import (
    ClusterCreate,
    ClusterListResponse,
    ClusterResponse,
    ClusterUpdate,
    ClusterWithLocations,
)
from app.services.audit_service import AuditService

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
    current_user: User = Depends(get_current_user),
) -> ClusterResponse:
    """Create a new cluster."""
    repo = ClusterRepository(db)
    audit = AuditService(db)
    
    # Check for duplicate name within the same company
    existing = await repo.get_by_name_and_company(data.name, current_user.company_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cluster with this name already exists",
        )
    
    # Auto-generate cluster_code
    cluster_code = generate_cluster_code()
    
    cluster = await repo.create(
        name=data.name,
        cluster_code=cluster_code,
        description=data.description,
        is_active=True,
        company_id=current_user.company_id,
    )
    
    # Audit log the creation
    await audit.log_create(
        entity_type="Cluster",
        entity_id=cluster.id,
        user_id=current_user.id,
        new_data={
            "name": data.name,
            "cluster_code": cluster_code,
            "description": data.description,
            "is_active": True,
        },
    )
    
    return ClusterResponse.model_validate(cluster)


@router.get(
    "",
    response_model=ClusterListResponse,
    summary="Get all clusters",
)
async def get_clusters(
    db: DBSession,
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> ClusterListResponse:
    """Get all clusters for the current user's company."""
    repo = ClusterRepository(db)
    clusters = await repo.get_by_company(current_user.company_id, skip, limit)
    total = await repo.count_by_company(current_user.company_id)
    
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
    current_user: User = Depends(get_current_user),
) -> ClusterWithLocations:
    """Get a cluster by ID with its locations."""
    repo = ClusterRepository(db)
    cluster = await repo.get_with_locations(cluster_id)
    
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )
    
    # Verify cluster belongs to user's company
    if cluster.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this cluster",
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
    current_user: User = Depends(get_current_user),
) -> ClusterResponse:
    """Update a cluster."""
    repo = ClusterRepository(db)
    audit = AuditService(db)
    
    update_data = data.model_dump(exclude_unset=True)
    
    # First verify the cluster belongs to this company
    existing_cluster = await repo.get_by_id(cluster_id)
    if not existing_cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )
    if existing_cluster.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this cluster",
        )
    
    # Capture old data for audit
    old_data = {
        "name": existing_cluster.name,
        "description": existing_cluster.description,
        "is_active": existing_cluster.is_active,
    }
    
    # Check for duplicate name if updating name
    if "name" in update_data:
        existing = await repo.get_by_name_and_company(update_data["name"], current_user.company_id)
        if existing and existing.id != cluster_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cluster with this name already exists",
            )
    
    cluster = await repo.update(cluster_id, **update_data)
    
    # Audit log the update
    await audit.log_update(
        entity_type="Cluster",
        entity_id=cluster_id,
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data,
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
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a cluster."""
    repo = ClusterRepository(db)
    audit = AuditService(db)
    
    # Verify cluster belongs to this company
    cluster = await repo.get_by_id(cluster_id)
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )
    if cluster.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this cluster",
        )
    
    # Capture old data for audit
    old_data = {
        "id": str(cluster.id),
        "name": cluster.name,
        "cluster_code": cluster.cluster_code,
        "description": cluster.description,
    }
    
    await repo.delete(cluster_id)
    
    # Audit log the deletion
    await audit.log_delete(
        entity_type="Cluster",
        entity_id=cluster_id,
        user_id=current_user.id,
        old_data=old_data,
    )

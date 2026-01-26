"""Seasons API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession
from app.models.season import SeasonStatus
from app.schemas.base import MessageResponse
from app.schemas.season import (
    SeasonCreate,
    SeasonListResponse,
    SeasonResponse,
    SeasonUpdate,
    SeasonWithWorkflow,
    WorkflowResponse,
)
from app.services.season_service import SeasonService

router = APIRouter(prefix="/seasons", tags=["Seasons"])


@router.post(
    "",
    response_model=SeasonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new season",
)
async def create_season(
    data: SeasonCreate,
    db: DBSession,
) -> SeasonResponse:
    """Create a new season with initial workflow state."""
    service = SeasonService(db)
    season = await service.create_season(data)
    return SeasonResponse.model_validate(season)


@router.get(
    "",
    response_model=SeasonListResponse,
    summary="Get all seasons",
)
async def get_seasons(
    db: DBSession,
    status_filter: Optional[SeasonStatus] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> SeasonListResponse:
    """Get all seasons with optional filtering."""
    service = SeasonService(db)
    seasons, total = await service.get_seasons(skip, limit, status_filter)
    
    return SeasonListResponse(
        items=[SeasonResponse.model_validate(s) for s in seasons],
        total=total,
    )


@router.get(
    "/{season_id}",
    response_model=SeasonWithWorkflow,
    summary="Get a season by ID",
)
async def get_season(
    season_id: UUID,
    db: DBSession,
) -> SeasonWithWorkflow:
    """Get a season by ID with workflow status."""
    service = SeasonService(db)
    season = await service.get_season(season_id)
    
    response = SeasonWithWorkflow.model_validate(season)
    if season.workflow:
        response.workflow = WorkflowResponse.model_validate(season.workflow)
    
    return response


@router.patch(
    "/{season_id}",
    response_model=SeasonResponse,
    summary="Update a season",
)
async def update_season(
    season_id: UUID,
    data: SeasonUpdate,
    db: DBSession,
) -> SeasonResponse:
    """Update a season."""
    service = SeasonService(db)
    season = await service.update_season(season_id, data)
    return SeasonResponse.model_validate(season)


@router.delete(
    "/{season_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a season",
)
async def delete_season(
    season_id: UUID,
    db: DBSession,
) -> None:
    """Delete a season and all related data."""
    service = SeasonService(db)
    await service.delete_season(season_id)


@router.get(
    "/{season_id}/workflow",
    response_model=WorkflowResponse,
    summary="Get season workflow status",
)
async def get_workflow(
    season_id: UUID,
    db: DBSession,
) -> WorkflowResponse:
    """Get workflow status for a season."""
    service = SeasonService(db)
    workflow = await service.get_workflow(season_id)
    return WorkflowResponse.model_validate(workflow)


@router.post(
    "/{season_id}/define-locations",
    response_model=WorkflowResponse,
    summary="Mark locations as defined",
)
async def define_locations(
    season_id: UUID,
    db: DBSession,
) -> WorkflowResponse:
    """Mark locations as defined for a season."""
    service = SeasonService(db)
    workflow = await service.mark_locations_defined(season_id)
    return WorkflowResponse.model_validate(workflow)


@router.post(
    "/{season_id}/lock",
    response_model=WorkflowResponse,
    summary="Lock a season",
)
async def lock_season(
    season_id: UUID,
    db: DBSession,
) -> WorkflowResponse:
    """Lock a season to prevent further modifications."""
    service = SeasonService(db)
    workflow = await service.lock_season(season_id)
    return WorkflowResponse.model_validate(workflow)

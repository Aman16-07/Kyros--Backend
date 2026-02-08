"""Seasons API endpoints with workflow management."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession, get_current_user
from app.models.season import SeasonStatus
from app.models.user import User
from app.schemas.base import MessageResponse
from app.schemas.season import (
    SeasonCreate,
    SeasonListResponse,
    SeasonResponse,
    SeasonUpdate,
    SeasonWithWorkflow,
    WorkflowResponse,
    WorkflowStatusResponse,
)
from app.services.season_service import SeasonService
from app.services.workflow_orchestrator import WorkflowOrchestrator

router = APIRouter(prefix="/seasons", tags=["Seasons"])


@router.post(
    "",
    response_model=SeasonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new season",
    description="""
    Create a new season with auto-generated season_code (format: XXXX-XXXX).
    
    This is Step 1 of the workflow. After creating a season, you must:
    1. Define locations
    2. Upload season plan
    3. Upload OTB plan
    4. Upload range intent
    5. Lock for read-only analytics
    """,
)
async def create_season(
    data: SeasonCreate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SeasonResponse:
    """Create a new season with initial workflow state."""
    # Inject current user as creator and company
    data.created_by = current_user.id
    data.company_id = current_user.company_id
    
    orchestrator = WorkflowOrchestrator(db)
    season = await orchestrator.create_season(data)
    return SeasonResponse.model_validate(season)


@router.get(
    "",
    response_model=SeasonListResponse,
    summary="Get all seasons",
)
async def get_seasons(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Optional[SeasonStatus] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> SeasonListResponse:
    """Get all seasons for the current user's company."""
    service = SeasonService(db)
    seasons, total = await service.get_seasons_by_company(
        current_user.company_id, skip, limit, status_filter
    )
    
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> SeasonResponse:
    """Update a season. Fails if season is locked."""
    service = SeasonService(db)
    
    # Check if season is locked (immutable)
    workflow = await service.get_workflow(season_id)
    if workflow and workflow.locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Season is locked and cannot be modified. Locked seasons are read-only.",
        )
    
    season = await service.update_season(season_id, data, user_id=current_user.id)
    return SeasonResponse.model_validate(season)


@router.delete(
    "/{season_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a season",
)
async def delete_season(
    season_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a season and all related data. Fails if season is locked."""
    service = SeasonService(db)
    
    # Check if season is locked (immutable)
    workflow = await service.get_workflow(season_id)
    if workflow and workflow.locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Season is locked and cannot be deleted. Locked seasons are read-only.",
        )
    
    await service.delete_season(season_id, user_id=current_user.id)


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
    summary="Complete location definition step",
    description="""
    Mark location definition as complete (Step 2).
    
    Prerequisites:
    - Season must be in CREATED status
    - Locations should have been created via /locations endpoint
    
    After this: Season moves to LOCATIONS_DEFINED status
    Next step: Upload Season Plan
    """,
)
async def complete_locations_defined(
    season_id: UUID,
    db: DBSession,
) -> WorkflowResponse:
    """Mark locations as defined for a season."""
    orchestrator = WorkflowOrchestrator(db)
    season = await orchestrator.complete_location_definition(season_id)
    workflow = await orchestrator.workflow_repo.get_by_season_id(season_id)
    return WorkflowResponse.model_validate(workflow)


@router.post(
    "/{season_id}/complete-plan-upload",
    response_model=WorkflowResponse,
    summary="Complete season plan upload step",
    description="""
    Mark season plan upload as complete (Step 3).
    
    Prerequisites:
    - Season must be in LOCATIONS_DEFINED status
    - Season plans should have been uploaded via /plans endpoint
    
    WARNING: Season plan becomes IMMUTABLE after this step!
    
    After this: Season moves to PLAN_UPLOADED status
    Next step: Upload OTB Plan
    """,
)
async def complete_plan_upload(
    season_id: UUID,
    db: DBSession,
) -> WorkflowResponse:
    """Mark season plan upload as complete."""
    orchestrator = WorkflowOrchestrator(db)
    season = await orchestrator.complete_plan_upload(season_id)
    workflow = await orchestrator.workflow_repo.get_by_season_id(season_id)
    return WorkflowResponse.model_validate(workflow)


@router.post(
    "/{season_id}/complete-otb-upload",
    response_model=WorkflowResponse,
    summary="Complete OTB plan upload step",
    description="""
    Mark OTB plan upload as complete (Step 4).
    
    Prerequisites:
    - Season must be in PLAN_UPLOADED status
    - OTB plans should have been uploaded via /otb endpoint
    
    OTB Formula: Planned Sales + Planned Closing Stock - Opening Stock - On Order
    
    After this: Season moves to OTB_UPLOADED status
    Next step: Upload Range Intent
    """,
)
async def complete_otb_upload(
    season_id: UUID,
    db: DBSession,
) -> WorkflowResponse:
    """Mark OTB upload as complete."""
    orchestrator = WorkflowOrchestrator(db)
    season = await orchestrator.complete_otb_upload(season_id)
    workflow = await orchestrator.workflow_repo.get_by_season_id(season_id)
    return WorkflowResponse.model_validate(workflow)


@router.post(
    "/{season_id}/complete-range-upload",
    response_model=WorkflowResponse,
    summary="Complete range intent upload step",
    description="""
    Mark range intent upload as complete (Step 5).
    
    Prerequisites:
    - Season must be in OTB_UPLOADED status
    - Range intents should have been uploaded via /range-intent endpoint
    
    After this: Season moves to RANGE_UPLOADED status
    Next step: Ingest POs/GRNs or Lock Season
    """,
)
async def complete_range_upload(
    season_id: UUID,
    db: DBSession,
) -> WorkflowResponse:
    """Mark range intent upload as complete."""
    orchestrator = WorkflowOrchestrator(db)
    season = await orchestrator.complete_range_upload(season_id)
    workflow = await orchestrator.workflow_repo.get_by_season_id(season_id)
    return WorkflowResponse.model_validate(workflow)


@router.post(
    "/{season_id}/lock",
    response_model=WorkflowResponse,
    summary="Lock season for read-only analytics",
    description="""
    Lock the season (Step 6 - Final).
    
    Prerequisites:
    - Season must be in RANGE_UPLOADED status
    
    WARNING: After locking, NO EDITING IS ALLOWED!
    The season becomes read-only for analytics purposes.
    
    After this: Season moves to LOCKED status
    Available: Read-Only Analytics View
    """,
)
async def lock_season(
    season_id: UUID,
    db: DBSession,
) -> WorkflowResponse:
    """Lock a season to prevent further modifications."""
    orchestrator = WorkflowOrchestrator(db)
    season = await orchestrator.lock_season(season_id)
    workflow = await orchestrator.workflow_repo.get_by_season_id(season_id)
    return WorkflowResponse.model_validate(workflow)


@router.get(
    "/{season_id}/workflow-status",
    response_model=WorkflowStatusResponse,
    summary="Get complete workflow status",
    description="Get detailed workflow status including current step, next action, and editability flags.",
)
async def get_workflow_status(
    season_id: UUID,
    db: DBSession,
) -> WorkflowStatusResponse:
    """Get complete workflow status for a season including editability information."""
    service = SeasonService(db)
    workflow = await service.get_workflow(season_id)
    workflow_response = WorkflowResponse.model_validate(workflow)
    return WorkflowStatusResponse.from_workflow(workflow_response)

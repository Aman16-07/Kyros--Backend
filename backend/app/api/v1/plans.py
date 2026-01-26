"""Season Plans API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession
from app.schemas.base import MessageResponse
from app.schemas.plan import (
    SeasonPlanApproveRequest,
    SeasonPlanBulkCreate,
    SeasonPlanCreate,
    SeasonPlanListResponse,
    SeasonPlanResponse,
    SeasonPlanUpdate,
)
from app.services.plan_service import SeasonPlanService

router = APIRouter(prefix="/plans", tags=["Season Plans"])


@router.post(
    "",
    response_model=SeasonPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new season plan",
)
async def create_plan(
    data: SeasonPlanCreate,
    db: DBSession,
) -> SeasonPlanResponse:
    """Create a new season plan."""
    service = SeasonPlanService(db)
    plan = await service.create_plan(data)
    return SeasonPlanResponse.model_validate(plan)


@router.post(
    "/bulk",
    response_model=SeasonPlanListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create season plans",
)
async def bulk_create_plans(
    data: SeasonPlanBulkCreate,
    db: DBSession,
) -> SeasonPlanListResponse:
    """Bulk create season plans (updates workflow to plan_uploaded)."""
    service = SeasonPlanService(db)
    plans = await service.bulk_create_plans(data.plans)
    
    return SeasonPlanListResponse(
        items=[SeasonPlanResponse.model_validate(p) for p in plans],
        total=len(plans),
    )


@router.get(
    "",
    response_model=SeasonPlanListResponse,
    summary="Get all season plans",
)
async def get_plans(
    db: DBSession,
    season_id: UUID = Query(..., description="Season ID (required)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> SeasonPlanListResponse:
    """Get all season plans for a season."""
    service = SeasonPlanService(db)
    plans, total = await service.get_plans_by_season(season_id, skip, limit)
    
    return SeasonPlanListResponse(
        items=[SeasonPlanResponse.model_validate(p) for p in plans],
        total=total,
    )


@router.get(
    "/{plan_id}",
    response_model=SeasonPlanResponse,
    summary="Get a season plan by ID",
)
async def get_plan(
    plan_id: UUID,
    db: DBSession,
) -> SeasonPlanResponse:
    """Get a season plan by ID."""
    service = SeasonPlanService(db)
    plan = await service.get_plan(plan_id)
    return SeasonPlanResponse.model_validate(plan)


@router.patch(
    "/{plan_id}",
    response_model=SeasonPlanResponse,
    summary="Update a season plan",
)
async def update_plan(
    plan_id: UUID,
    data: SeasonPlanUpdate,
    db: DBSession,
) -> SeasonPlanResponse:
    """Update a season plan."""
    service = SeasonPlanService(db)
    plan = await service.update_plan(plan_id, data)
    return SeasonPlanResponse.model_validate(plan)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a season plan",
)
async def delete_plan(
    plan_id: UUID,
    db: DBSession,
) -> None:
    """Delete a season plan."""
    service = SeasonPlanService(db)
    await service.delete_plan(plan_id)


@router.post(
    "/approve",
    response_model=MessageResponse,
    summary="Approve season plans",
)
async def approve_plans(
    data: SeasonPlanApproveRequest,
    db: DBSession,
) -> MessageResponse:
    """Approve or reject multiple season plans."""
    service = SeasonPlanService(db)
    count = await service.approve_plans(data.plan_ids, data.approved)
    
    action = "approved" if data.approved else "rejected"
    return MessageResponse(
        message=f"Successfully {action} {count} plan(s)",
        success=True,
    )

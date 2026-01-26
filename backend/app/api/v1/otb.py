"""OTB Plans API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession
from app.schemas.otb import (
    OTBPlanBulkCreate,
    OTBPlanCreate,
    OTBPlanListResponse,
    OTBPlanResponse,
    OTBPlanUpdate,
    OTBSummary,
)
from app.services.otb_service import OTBService

router = APIRouter(prefix="/otb", tags=["OTB Plans"])


@router.post(
    "",
    response_model=OTBPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new OTB plan",
)
async def create_otb_plan(
    data: OTBPlanCreate,
    db: DBSession,
) -> OTBPlanResponse:
    """Create a new OTB plan."""
    service = OTBService(db)
    plan = await service.create_otb_plan(data)
    return OTBPlanResponse.model_validate(plan)


@router.post(
    "/bulk",
    response_model=OTBPlanListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create OTB plans",
)
async def bulk_create_otb_plans(
    data: OTBPlanBulkCreate,
    db: DBSession,
) -> OTBPlanListResponse:
    """Bulk create OTB plans (updates workflow to otb_uploaded)."""
    service = OTBService(db)
    plans = await service.bulk_create_otb_plans(data.plans)
    
    return OTBPlanListResponse(
        items=[OTBPlanResponse.model_validate(p) for p in plans],
        total=len(plans),
    )


@router.get(
    "",
    response_model=OTBPlanListResponse,
    summary="Get all OTB plans",
)
async def get_otb_plans(
    db: DBSession,
    season_id: UUID = Query(..., description="Season ID (required)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> OTBPlanListResponse:
    """Get all OTB plans for a season."""
    service = OTBService(db)
    plans, total = await service.get_otb_plans_by_season(season_id, skip, limit)
    
    return OTBPlanListResponse(
        items=[OTBPlanResponse.model_validate(p) for p in plans],
        total=total,
    )


@router.get(
    "/summary",
    response_model=list[OTBSummary],
    summary="Get OTB summary by month",
)
async def get_otb_summary(
    db: DBSession,
    season_id: UUID = Query(..., description="Season ID"),
) -> list[OTBSummary]:
    """Get OTB summary grouped by month."""
    service = OTBService(db)
    return await service.get_otb_summary(season_id)


@router.get(
    "/{plan_id}",
    response_model=OTBPlanResponse,
    summary="Get an OTB plan by ID",
)
async def get_otb_plan(
    plan_id: UUID,
    db: DBSession,
) -> OTBPlanResponse:
    """Get an OTB plan by ID."""
    service = OTBService(db)
    plan = await service.get_otb_plan(plan_id)
    return OTBPlanResponse.model_validate(plan)


@router.patch(
    "/{plan_id}",
    response_model=OTBPlanResponse,
    summary="Update an OTB plan",
)
async def update_otb_plan(
    plan_id: UUID,
    data: OTBPlanUpdate,
    db: DBSession,
) -> OTBPlanResponse:
    """Update an OTB plan."""
    service = OTBService(db)
    plan = await service.update_otb_plan(plan_id, data)
    return OTBPlanResponse.model_validate(plan)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an OTB plan",
)
async def delete_otb_plan(
    plan_id: UUID,
    db: DBSession,
) -> None:
    """Delete an OTB plan."""
    service = OTBService(db)
    await service.delete_otb_plan(plan_id)

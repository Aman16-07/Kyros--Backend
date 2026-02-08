"""Season Plans API endpoints."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession, get_current_user
from app.models.user import User
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> SeasonPlanResponse:
    """Create a new season plan."""
    # Inject current user as uploader
    data.uploaded_by = current_user.id
    
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> SeasonPlanListResponse:
    """Bulk create season plans (updates workflow to plan_uploaded)."""
    # Inject current user as uploader for all plans
    for plan in data.plans:
        plan.uploaded_by = current_user.id
    
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
    description="""
    Update a season plan. Fails if:
    - Season is locked
    - Plan is approved (approved plans are immutable)
    - Workflow has progressed past plan upload step
    """,
)
async def update_plan(
    plan_id: UUID,
    data: SeasonPlanUpdate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SeasonPlanResponse:
    """Update a season plan. Approved plans cannot be modified."""
    service = SeasonPlanService(db)
    plan = await service.update_plan(plan_id, data, user_id=current_user.id)
    return SeasonPlanResponse.model_validate(plan)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a season plan",
    description="""
    Delete a season plan. Fails if:
    - Season is locked
    - Plan is approved (approved plans are immutable)
    - Workflow has progressed past plan upload step
    """,
)
async def delete_plan(
    plan_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a season plan. Approved plans cannot be deleted."""
    service = SeasonPlanService(db)
    await service.delete_plan(plan_id, user_id=current_user.id)
    service = SeasonPlanService(db)
    await service.delete_plan(plan_id)


@router.post(
    "/preview",
    response_model=dict,
    summary="Preview season plan upload without committing",
)
async def preview_season_plans(
    data: SeasonPlanBulkCreate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Validate season plan data without saving to database.
    
    Use this endpoint to preview the results of a bulk upload:
    - Validates all records against schema
    - Checks for missing location/category references
    - Returns validation errors
    - Does NOT commit any changes
    
    Returns:
        - valid_count: Number of records that would be created
        - error_count: Number of validation errors
        - errors: List of error messages
        - preview: First 10 valid records for preview
    """
    from app.repositories.location_repo import LocationRepository
    from app.repositories.category_repo import CategoryRepository
    
    location_repo = LocationRepository(db)
    category_repo = CategoryRepository(db)
    
    valid_records = []
    errors = []
    
    for idx, plan_data in enumerate(data.plans):
        try:
            # Validate location exists
            location = await location_repo.get_by_id(plan_data.location_id)
            if not location:
                errors.append({
                    "row": idx + 1,
                    "field": "location_id",
                    "message": f"Location {plan_data.location_id} not found",
                })
                continue
            
            # Validate category exists
            category = await category_repo.get_by_id(plan_data.category_id)
            if not category:
                errors.append({
                    "row": idx + 1,
                    "field": "category_id",
                    "message": f"Category {plan_data.category_id} not found",
                })
                continue
            
            valid_records.append({
                "row": idx + 1,
                "season_id": str(plan_data.season_id),
                "location_id": str(plan_data.location_id),
                "location_name": location.name,
                "category_id": str(plan_data.category_id),
                "category_name": category.name,
                "planned_sales": float(plan_data.planned_sales),
                "planned_margin": float(plan_data.planned_margin),
                "inventory_turns": float(plan_data.inventory_turns),
            })
        except Exception as e:
            errors.append({
                "row": idx + 1,
                "message": str(e),
            })
    
    return {
        "valid_count": len(valid_records),
        "error_count": len(errors),
        "errors": errors,
        "preview": valid_records[:10],  # First 10 records for preview
    }


@router.post(
    "/approve",
    response_model=MessageResponse,
    summary="Approve season plans",
    description="""
    Approve season plans. WARNING: Once approved, plans become IMMUTABLE.
    Approved plans cannot be edited, deleted, or un-approved.
    """,
)
async def approve_plans(
    data: SeasonPlanApproveRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessageResponse:
    """Approve season plans. Once approved, plans are IMMUTABLE."""
    service = SeasonPlanService(db)
    count = await service.approve_plans(data.plan_ids, data.approved, user_id=current_user.id)
    
    action = "approved" if data.approved else "rejected"
    return MessageResponse(
        message=f"Successfully {action} {count} plan(s)",
        success=True,
    )

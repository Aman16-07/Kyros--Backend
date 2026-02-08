"""OTB Plans API endpoints."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession, get_current_user
from app.models.user import User
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> OTBPlanResponse:
    """Create a new OTB plan."""
    # Inject current user as uploader
    data.uploaded_by = current_user.id
    
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> OTBPlanListResponse:
    """Bulk create OTB plans (updates workflow to otb_uploaded)."""
    # Inject current user as uploader for all plans
    for plan in data.plans:
        plan.uploaded_by = current_user.id
    
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


@router.post(
    "/preview",
    response_model=dict,
    summary="Preview OTB plan upload without committing",
)
async def preview_otb_plans(
    data: OTBPlanBulkCreate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Validate OTB plan data without saving to database.
    
    Use this endpoint to preview the results of a bulk upload:
    - Validates all records against schema
    - Calculates OTB values using formula
    - Checks for duplicates
    - Returns validation errors
    - Does NOT commit any changes
    
    Returns:
        - valid_count: Number of records that would be created
        - duplicate_count: Number of duplicates found
        - error_count: Number of validation errors
        - errors: List of error messages
        - preview: First 10 valid records with calculated OTB
    """
    from app.repositories.location_repo import LocationRepository
    from app.repositories.category_repo import CategoryRepository
    from app.repositories.otb_repo import OTBPlanRepository
    from decimal import Decimal
    
    location_repo = LocationRepository(db)
    category_repo = CategoryRepository(db)
    otb_repo = OTBPlanRepository(db)
    
    valid_records = []
    duplicates = []
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
            
            # Check for duplicates
            existing = await otb_repo.get_by_composite_key(
                plan_data.season_id,
                plan_data.location_id,
                plan_data.category_id,
                plan_data.month.replace(day=1),
            )
            if existing:
                duplicates.append({
                    "row": idx + 1,
                    "message": f"OTB plan already exists for this combination",
                })
                continue
            
            # Calculate OTB using formula
            calculated_otb = (
                plan_data.planned_sales + 
                plan_data.planned_closing_stock - 
                plan_data.opening_stock - 
                plan_data.on_order
            )
            
            valid_records.append({
                "row": idx + 1,
                "season_id": str(plan_data.season_id),
                "location_id": str(plan_data.location_id),
                "location_name": location.name,
                "category_id": str(plan_data.category_id),
                "category_name": category.name,
                "month": plan_data.month.isoformat(),
                "planned_sales": float(plan_data.planned_sales),
                "planned_closing_stock": float(plan_data.planned_closing_stock),
                "opening_stock": float(plan_data.opening_stock),
                "on_order": float(plan_data.on_order),
                "calculated_otb": float(calculated_otb),
            })
        except Exception as e:
            errors.append({
                "row": idx + 1,
                "message": str(e),
            })
    
    return {
        "valid_count": len(valid_records),
        "duplicate_count": len(duplicates),
        "error_count": len(errors),
        "duplicates": duplicates,
        "errors": errors,
        "preview": valid_records[:10],
    }


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
    description="""
    Update an OTB plan. Fails if:
    - Season is locked
    - Workflow has progressed past OTB upload step
    """,
)
async def update_otb_plan(
    plan_id: UUID,
    data: OTBPlanUpdate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> OTBPlanResponse:
    """Update an OTB plan."""
    service = OTBService(db)
    plan = await service.update_otb_plan(plan_id, data, user_id=current_user.id)
    return OTBPlanResponse.model_validate(plan)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an OTB plan",
    description="""
    Delete an OTB plan. Fails if:
    - Season is locked
    - Workflow has progressed past OTB upload step
    """,
)
async def delete_otb_plan(
    plan_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete an OTB plan."""
    service = OTBService(db)
    await service.delete_otb_plan(plan_id, user_id=current_user.id)

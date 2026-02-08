"""Range Intent API endpoints."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession, get_current_user
from app.models.user import User
from app.schemas.range_intent import (
    RangeIntentBulkCreate,
    RangeIntentCreate,
    RangeIntentListResponse,
    RangeIntentResponse,
    RangeIntentUpdate,
)
from app.services.range_intent_service import RangeIntentService

router = APIRouter(prefix="/range-intent", tags=["Range Intent"])


@router.post(
    "",
    response_model=RangeIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new range intent",
)
async def create_range_intent(
    data: RangeIntentCreate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> RangeIntentResponse:
    """Create a new range intent."""
    # Inject current user as uploader
    data.uploaded_by = current_user.id
    
    service = RangeIntentService(db)
    intent = await service.create_range_intent(data)
    return RangeIntentResponse.model_validate(intent)


@router.post(
    "/bulk",
    response_model=RangeIntentListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create range intents",
)
async def bulk_create_range_intents(
    data: RangeIntentBulkCreate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> RangeIntentListResponse:
    """Bulk create range intents (updates workflow to range_uploaded)."""
    # Inject current user as uploader for all intents
    for intent in data.intents:
        intent.uploaded_by = current_user.id
    
    service = RangeIntentService(db)
    intents = await service.bulk_create_range_intents(data.intents)
    
    return RangeIntentListResponse(
        items=[RangeIntentResponse.model_validate(i) for i in intents],
        total=len(intents),
    )


@router.get(
    "",
    response_model=RangeIntentListResponse,
    summary="Get all range intents",
)
async def get_range_intents(
    db: DBSession,
    season_id: UUID = Query(..., description="Season ID (required)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> RangeIntentListResponse:
    """Get all range intents for a season."""
    service = RangeIntentService(db)
    intents, total = await service.get_range_intents_by_season(season_id, skip, limit)
    
    return RangeIntentListResponse(
        items=[RangeIntentResponse.model_validate(i) for i in intents],
        total=total,
    )


@router.post(
    "/preview",
    response_model=dict,
    summary="Preview range intent upload without committing",
)
async def preview_range_intents(
    data: RangeIntentBulkCreate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Validate range intent data without saving to database.
    
    Use this endpoint to preview the results of a bulk upload:
    - Validates all records against schema
    - Validates core + fashion = 100%
    - Checks for duplicates
    - Returns validation errors
    - Does NOT commit any changes
    
    Returns:
        - valid_count: Number of records that would be created
        - duplicate_count: Number of duplicates found
        - error_count: Number of validation errors
        - errors: List of error messages
        - preview: First 10 valid records for preview
    """
    from app.repositories.category_repo import CategoryRepository
    from app.repositories.range_intent_repo import RangeIntentRepository
    from decimal import Decimal
    
    category_repo = CategoryRepository(db)
    range_repo = RangeIntentRepository(db)
    
    valid_records = []
    duplicates = []
    errors = []
    
    for idx, intent_data in enumerate(data.intents):
        try:
            # Validate category exists
            category = await category_repo.get_by_id(intent_data.category_id)
            if not category:
                errors.append({
                    "row": idx + 1,
                    "field": "category_id",
                    "message": f"Category {intent_data.category_id} not found",
                })
                continue
            
            # Validate core + fashion = 100
            total_percent = intent_data.core_percent + intent_data.fashion_percent
            if total_percent != Decimal("100.00"):
                errors.append({
                    "row": idx + 1,
                    "field": "core_percent/fashion_percent",
                    "message": f"core_percent + fashion_percent must equal 100, got {total_percent}",
                })
                continue
            
            # Check for duplicates
            existing = await range_repo.get_by_season_and_category(
                intent_data.season_id,
                intent_data.category_id,
            )
            if existing:
                duplicates.append({
                    "row": idx + 1,
                    "message": f"Range intent already exists for this season/category (will be updated)",
                })
            
            valid_records.append({
                "row": idx + 1,
                "season_id": str(intent_data.season_id),
                "category_id": str(intent_data.category_id),
                "category_name": category.name,
                "core_percent": float(intent_data.core_percent),
                "fashion_percent": float(intent_data.fashion_percent),
                "price_band_mix": intent_data.price_band_mix,
                "will_update": existing is not None,
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
    "/{intent_id}",
    response_model=RangeIntentResponse,
    summary="Get a range intent by ID",
)
async def get_range_intent(
    intent_id: UUID,
    db: DBSession,
) -> RangeIntentResponse:
    """Get a range intent by ID."""
    service = RangeIntentService(db)
    intent = await service.get_range_intent(intent_id)
    return RangeIntentResponse.model_validate(intent)


@router.patch(
    "/{intent_id}",
    response_model=RangeIntentResponse,
    summary="Update a range intent",
    description="""
    Update a range intent. Fails if:
    - Season is locked
    - Workflow has progressed past range upload step
    """,
)
async def update_range_intent(
    intent_id: UUID,
    data: RangeIntentUpdate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> RangeIntentResponse:
    """Update a range intent."""
    service = RangeIntentService(db)
    intent = await service.update_range_intent(intent_id, data, user_id=current_user.id)
    return RangeIntentResponse.model_validate(intent)


@router.delete(
    "/{intent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a range intent",
    description="""
    Delete a range intent. Fails if:
    - Season is locked
    - Workflow has progressed past range upload step
    """,
)
async def delete_range_intent(
    intent_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a range intent."""
    service = RangeIntentService(db)
    await service.delete_range_intent(intent_id, user_id=current_user.id)

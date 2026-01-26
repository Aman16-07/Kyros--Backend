"""Range Intent API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession
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
) -> RangeIntentResponse:
    """Create a new range intent."""
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
) -> RangeIntentListResponse:
    """Bulk create range intents (updates workflow to range_uploaded)."""
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
)
async def update_range_intent(
    intent_id: UUID,
    data: RangeIntentUpdate,
    db: DBSession,
) -> RangeIntentResponse:
    """Update a range intent."""
    service = RangeIntentService(db)
    intent = await service.update_range_intent(intent_id, data)
    return RangeIntentResponse.model_validate(intent)


@router.delete(
    "/{intent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a range intent",
)
async def delete_range_intent(
    intent_id: UUID,
    db: DBSession,
) -> None:
    """Delete a range intent."""
    service = RangeIntentService(db)
    await service.delete_range_intent(intent_id)

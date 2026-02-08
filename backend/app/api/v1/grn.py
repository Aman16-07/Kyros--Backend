"""GRN Records API endpoints."""

from datetime import date
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession, get_current_user
from app.models.user import User
from app.schemas.grn import (
    GRNRecordBulkCreate,
    GRNRecordCreate,
    GRNRecordListResponse,
    GRNRecordResponse,
    GRNRecordUpdate,
    GRNSummary,
)
from app.services.grn_ingest_service import GRNIngestService

router = APIRouter(prefix="/grn", tags=["GRN Records"])


@router.post(
    "",
    response_model=GRNRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new GRN record",
)
async def create_grn_record(
    data: GRNRecordCreate,
    db: DBSession,
) -> GRNRecordResponse:
    """Create a new GRN record."""
    service = GRNIngestService(db)
    grn = await service.create_grn_record(data)
    return GRNRecordResponse.model_validate(grn)


@router.post(
    "/bulk",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create GRN records",
)
async def bulk_create_grn_records(
    data: GRNRecordBulkCreate,
    db: DBSession,
) -> dict:
    """Bulk create GRN records from CSV data."""
    service = GRNIngestService(db)
    created, errors = await service.bulk_create_from_csv(data.records)
    
    return {
        "created": len(created),
        "errors": errors,
        "items": [GRNRecordResponse.model_validate(grn) for grn in created],
    }


@router.get(
    "",
    response_model=GRNRecordListResponse,
    summary="Get all GRN records",
)
async def get_grn_records(
    db: DBSession,
    po_id: Optional[UUID] = Query(None, description="Filter by purchase order"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> GRNRecordListResponse:
    """Get all GRN records with optional filtering."""
    service = GRNIngestService(db)
    
    if po_id:
        records, total = await service.get_grn_records_by_po(po_id, skip, limit)
    elif start_date and end_date:
        records, total = await service.get_grn_records_by_date_range(
            start_date, end_date, skip, limit
        )
    else:
        # Get all records (no filter) - for dashboard views
        records, total = await service.get_all_grn_records(skip, limit)
    
    return GRNRecordListResponse(
        items=[GRNRecordResponse.model_validate(grn) for grn in records],
        total=total,
    )


@router.get(
    "/summary",
    response_model=GRNSummary,
    summary="Get GRN summary",
)
async def get_grn_summary(
    db: DBSession,
    po_ids: Optional[list[UUID]] = Query(None, description="Filter by PO IDs"),
) -> GRNSummary:
    """Get GRN summary."""
    service = GRNIngestService(db)
    return await service.get_summary(po_ids)


@router.get(
    "/fulfillment/{po_id}",
    summary="Get fulfillment status for a PO",
)
async def get_fulfillment_status(
    po_id: UUID,
    db: DBSession,
) -> dict:
    """Get fulfillment status for a purchase order."""
    service = GRNIngestService(db)
    return await service.get_fulfillment_status(po_id)


@router.get(
    "/{grn_id}",
    response_model=GRNRecordResponse,
    summary="Get a GRN record by ID",
)
async def get_grn_record(
    grn_id: UUID,
    db: DBSession,
) -> GRNRecordResponse:
    """Get a GRN record by ID."""
    service = GRNIngestService(db)
    grn = await service.get_grn_record(grn_id)
    return GRNRecordResponse.model_validate(grn)


@router.patch(
    "/{grn_id}",
    response_model=GRNRecordResponse,
    summary="Update a GRN record",
    description="""
    Update a GRN record. Fails if the season is locked.
    Locked seasons = all data is read-only.
    """,
)
async def update_grn_record(
    grn_id: UUID,
    data: GRNRecordUpdate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> GRNRecordResponse:
    """Update a GRN record. Fails if season is locked."""
    service = GRNIngestService(db)
    grn = await service.update_grn_record(grn_id, data, user_id=current_user.id)
    return GRNRecordResponse.model_validate(grn)


@router.delete(
    "/{grn_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a GRN record",
    description="""
    Delete a GRN record. Fails if the season is locked.
    Locked seasons = all data is read-only.
    """,
)
async def delete_grn_record(
    grn_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a GRN record. Fails if season is locked."""
    service = GRNIngestService(db)
    await service.delete_grn_record(grn_id, user_id=current_user.id)

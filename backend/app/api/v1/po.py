"""Purchase Orders API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status

from app.core.deps import DBSession
from app.models.purchase_order import POSource
from app.schemas.base import MessageResponse
from app.schemas.po import (
    POSummary,
    PurchaseOrderBulkCreate,
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
)
from app.services.po_ingest_service import POIngestService

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new purchase order",
)
async def create_purchase_order(
    data: PurchaseOrderCreate,
    db: DBSession,
) -> PurchaseOrderResponse:
    """Create a new purchase order."""
    service = POIngestService(db)
    po = await service.create_purchase_order(data)
    return PurchaseOrderResponse.model_validate(po)


@router.post(
    "/bulk",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create purchase orders",
)
async def bulk_create_purchase_orders(
    data: PurchaseOrderBulkCreate,
    db: DBSession,
) -> dict:
    """Bulk create purchase orders from CSV data."""
    service = POIngestService(db)
    created, errors = await service.bulk_create_from_csv(data.orders)
    
    return {
        "created": len(created),
        "errors": errors,
        "items": [PurchaseOrderResponse.model_validate(po) for po in created],
    }


@router.get(
    "",
    response_model=PurchaseOrderListResponse,
    summary="Get all purchase orders",
)
async def get_purchase_orders(
    db: DBSession,
    season_id: Optional[UUID] = Query(None, description="Filter by season"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> PurchaseOrderListResponse:
    """Get all purchase orders with optional filtering."""
    service = POIngestService(db)
    orders, total = await service.get_purchase_orders(season_id, location_id, skip, limit)
    
    return PurchaseOrderListResponse(
        items=[PurchaseOrderResponse.model_validate(po) for po in orders],
        total=total,
    )


@router.get(
    "/summary",
    response_model=POSummary,
    summary="Get purchase order summary",
)
async def get_po_summary(
    db: DBSession,
    season_id: Optional[UUID] = Query(None, description="Filter by season"),
) -> POSummary:
    """Get purchase order summary."""
    service = POIngestService(db)
    return await service.get_summary(season_id)


@router.get(
    "/by-number/{po_number}",
    response_model=PurchaseOrderResponse,
    summary="Get a purchase order by PO number",
)
async def get_purchase_order_by_number(
    po_number: str,
    db: DBSession,
) -> PurchaseOrderResponse:
    """Get a purchase order by PO number."""
    service = POIngestService(db)
    po = await service.get_purchase_order_by_number(po_number)
    return PurchaseOrderResponse.model_validate(po)


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    summary="Get a purchase order by ID",
)
async def get_purchase_order(
    po_id: UUID,
    db: DBSession,
) -> PurchaseOrderResponse:
    """Get a purchase order by ID."""
    service = POIngestService(db)
    po = await service.get_purchase_order(po_id)
    return PurchaseOrderResponse.model_validate(po)


@router.patch(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    summary="Update a purchase order",
)
async def update_purchase_order(
    po_id: UUID,
    data: PurchaseOrderUpdate,
    db: DBSession,
) -> PurchaseOrderResponse:
    """Update a purchase order."""
    service = POIngestService(db)
    po = await service.update_purchase_order(po_id, data)
    return PurchaseOrderResponse.model_validate(po)


@router.delete(
    "/{po_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a purchase order",
)
async def delete_purchase_order(
    po_id: UUID,
    db: DBSession,
) -> None:
    """Delete a purchase order."""
    service = POIngestService(db)
    await service.delete_purchase_order(po_id)

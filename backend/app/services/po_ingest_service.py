"""Purchase Order ingest service - business logic for PO management."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase_order import POSource, PurchaseOrder
from app.repositories.po_repo import PurchaseOrderRepository
from app.schemas.po import POSummary, PurchaseOrderCreate, PurchaseOrderUpdate


class POIngestService:
    """Service for purchase order business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PurchaseOrderRepository(session)
    
    async def create_purchase_order(
        self,
        data: PurchaseOrderCreate,
    ) -> PurchaseOrder:
        """Create a new purchase order."""
        # Check for duplicate PO number
        existing = await self.repo.get_by_po_number(data.po_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Purchase order with number {data.po_number} already exists",
            )
        
        po = await self.repo.create(
            po_number=data.po_number,
            season_id=data.season_id,
            location_id=data.location_id,
            category_id=data.category_id,
            po_value=data.po_value,
            source=data.source,
        )
        
        return po
    
    async def bulk_create_from_csv(
        self,
        orders: list[PurchaseOrderCreate],
    ) -> tuple[list[PurchaseOrder], list[str]]:
        """Bulk create purchase orders from CSV data."""
        created_orders = []
        errors = []
        
        for order_data in orders:
            try:
                # Check for duplicate
                existing = await self.repo.get_by_po_number(order_data.po_number)
                if existing:
                    errors.append(f"PO {order_data.po_number} already exists")
                    continue
                
                po = await self.repo.create(
                    po_number=order_data.po_number,
                    season_id=order_data.season_id,
                    location_id=order_data.location_id,
                    category_id=order_data.category_id,
                    po_value=order_data.po_value,
                    source=POSource.CSV,
                )
                created_orders.append(po)
            except Exception as e:
                errors.append(f"Error creating PO {order_data.po_number}: {str(e)}")
        
        return created_orders, errors
    
    async def get_purchase_order(self, po_id: UUID) -> PurchaseOrder:
        """Get a purchase order by ID."""
        po = await self.repo.get_with_details(po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        return po
    
    async def get_purchase_order_by_number(
        self,
        po_number: str,
    ) -> PurchaseOrder:
        """Get a purchase order by PO number."""
        po = await self.repo.get_by_po_number(po_number)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        return po
    
    async def get_purchase_orders(
        self,
        season_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[PurchaseOrder], int]:
        """Get purchase orders with optional filtering."""
        if season_id:
            orders = await self.repo.get_by_season(season_id, skip, limit)
            total = await self.repo.count(season_id=season_id)
        elif location_id:
            orders = await self.repo.get_by_location(location_id, skip, limit)
            total = await self.repo.count(location_id=location_id)
        else:
            orders = await self.repo.get_all(skip, limit)
            total = await self.repo.count()
        
        return orders, total
    
    async def get_summary(
        self,
        season_id: Optional[UUID] = None,
    ) -> POSummary:
        """Get PO summary."""
        summary = await self.repo.get_summary(season_id)
        return POSummary(
            total_orders=summary["total_orders"],
            total_value=summary["total_value"],
            by_source=summary["by_source"],
        )
    
    async def update_purchase_order(
        self,
        po_id: UUID,
        data: PurchaseOrderUpdate,
    ) -> PurchaseOrder:
        """Update a purchase order."""
        po = await self.repo.get_by_id(po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        
        update_data = data.model_dump(exclude_unset=True)
        updated_po = await self.repo.update(po_id, **update_data)
        
        return updated_po
    
    async def delete_purchase_order(self, po_id: UUID) -> bool:
        """Delete a purchase order."""
        deleted = await self.repo.delete(po_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        return True

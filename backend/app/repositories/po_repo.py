"""Purchase Order repository."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase_order import POSource, PurchaseOrder
from app.repositories.base_repo import BaseRepository


class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    """Repository for PurchaseOrder model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PurchaseOrder, session)
    
    async def get_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get purchase order by PO number."""
        result = await self.session.execute(
            select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
        )
        return result.scalar_one_or_none()
    
    async def get_by_season(
        self,
        season_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PurchaseOrder]:
        """Get purchase orders by season."""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.season_id == season_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_location(
        self,
        location_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PurchaseOrder]:
        """Get purchase orders by location."""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.location_id == location_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_source(
        self,
        source: POSource,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PurchaseOrder]:
        """Get purchase orders by source."""
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.source == source)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_summary(self, season_id: Optional[UUID] = None) -> dict:
        """Get summary of purchase orders."""
        query = select(
            func.count(PurchaseOrder.id).label("total_orders"),
            func.sum(PurchaseOrder.po_value).label("total_value"),
        )
        
        if season_id:
            query = query.where(PurchaseOrder.season_id == season_id)
        
        result = await self.session.execute(query)
        row = result.one()
        
        # Get by source breakdown
        source_query = select(
            PurchaseOrder.source,
            func.count(PurchaseOrder.id).label("count"),
        ).group_by(PurchaseOrder.source)
        
        if season_id:
            source_query = source_query.where(PurchaseOrder.season_id == season_id)
        
        source_result = await self.session.execute(source_query)
        by_source = {str(r.source.value): r.count for r in source_result.all()}
        
        return {
            "total_orders": row.total_orders or 0,
            "total_value": row.total_value or Decimal("0.00"),
            "by_source": by_source,
        }
    
    async def get_with_details(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get purchase order with related entities."""
        result = await self.session.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.season),
                selectinload(PurchaseOrder.location),
                selectinload(PurchaseOrder.category),
                selectinload(PurchaseOrder.grn_records),
            )
            .where(PurchaseOrder.id == po_id)
        )
        return result.scalar_one_or_none()
    
    async def get_with_grn(
        self,
        season_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PurchaseOrder]:
        """Get purchase orders with GRN records."""
        result = await self.session.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.grn_records))
            .where(PurchaseOrder.season_id == season_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

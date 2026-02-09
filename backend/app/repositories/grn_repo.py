"""GRN Record repository."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import month_trunc

from app.models.grn import GRNRecord
from app.repositories.base_repo import BaseRepository


class GRNRecordRepository(BaseRepository[GRNRecord]):
    """Repository for GRNRecord model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(GRNRecord, session)
    
    async def get_by_po(
        self,
        po_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[GRNRecord]:
        """Get GRN records by purchase order."""
        result = await self.session.execute(
            select(GRNRecord)
            .where(GRNRecord.po_id == po_id)
            .order_by(GRNRecord.grn_date)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100,
    ) -> list[GRNRecord]:
        """Get GRN records within a date range."""
        result = await self.session.execute(
            select(GRNRecord)
            .where(
                GRNRecord.grn_date >= start_date,
                GRNRecord.grn_date <= end_date,
            )
            .order_by(GRNRecord.grn_date)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_total_received_for_po(self, po_id: UUID) -> Decimal:
        """Get total received value for a purchase order."""
        result = await self.session.execute(
            select(func.sum(GRNRecord.received_value))
            .where(GRNRecord.po_id == po_id)
        )
        return result.scalar() or Decimal("0.00")
    
    async def get_summary(self, po_ids: Optional[list[UUID]] = None) -> dict:
        """Get summary of GRN records."""
        query = select(
            func.count(GRNRecord.id).label("total_records"),
            func.sum(GRNRecord.received_value).label("total_value"),
        )
        
        if po_ids:
            query = query.where(GRNRecord.po_id.in_(po_ids))
        
        result = await self.session.execute(query)
        row = result.one()
        
        # Get by month breakdown
        month_query = select(
            month_trunc(GRNRecord.grn_date).label("month"),
            func.sum(GRNRecord.received_value).label("value"),
        ).group_by(month_trunc(GRNRecord.grn_date))
        
        if po_ids:
            month_query = month_query.where(GRNRecord.po_id.in_(po_ids))
        
        month_result = await self.session.execute(month_query)
        by_month = {
            str(r.month.strftime("%Y-%m") if r.month else "unknown"): r.value or Decimal("0.00")
            for r in month_result.all()
        }
        
        return {
            "total_records": row.total_records or 0,
            "total_received_value": row.total_value or Decimal("0.00"),
            "by_month": by_month,
        }
    
    async def get_with_po(self, grn_id: UUID) -> Optional[GRNRecord]:
        """Get GRN record with purchase order details."""
        result = await self.session.execute(
            select(GRNRecord)
            .options(selectinload(GRNRecord.purchase_order))
            .where(GRNRecord.id == grn_id)
        )
        return result.scalar_one_or_none()

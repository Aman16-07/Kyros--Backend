"""GRN Record ingest service - business logic for GRN management."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grn import GRNRecord
from app.repositories.grn_repo import GRNRecordRepository
from app.repositories.po_repo import PurchaseOrderRepository
from app.schemas.grn import GRNRecordCreate, GRNRecordUpdate, GRNSummary


class GRNIngestService:
    """Service for GRN record business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = GRNRecordRepository(session)
        self.po_repo = PurchaseOrderRepository(session)
    
    async def create_grn_record(self, data: GRNRecordCreate) -> GRNRecord:
        """Create a new GRN record."""
        # Verify PO exists
        po = await self.po_repo.get_by_id(data.po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        
        # Optionally check if received value exceeds PO value
        total_received = await self.repo.get_total_received_for_po(data.po_id)
        if total_received + data.received_value > po.po_value:
            # Warning but still allow (business may decide)
            pass
        
        grn = await self.repo.create(
            po_id=data.po_id,
            grn_date=data.grn_date,
            received_value=data.received_value,
        )
        
        return grn
    
    async def bulk_create_from_csv(
        self,
        records: list[GRNRecordCreate],
    ) -> tuple[list[GRNRecord], list[str]]:
        """Bulk create GRN records from CSV data."""
        created_records = []
        errors = []
        
        for record_data in records:
            try:
                # Verify PO exists
                po = await self.po_repo.get_by_id(record_data.po_id)
                if not po:
                    errors.append(f"PO {record_data.po_id} not found")
                    continue
                
                grn = await self.repo.create(
                    po_id=record_data.po_id,
                    grn_date=record_data.grn_date,
                    received_value=record_data.received_value,
                )
                created_records.append(grn)
            except Exception as e:
                errors.append(f"Error creating GRN for PO {record_data.po_id}: {str(e)}")
        
        return created_records, errors
    
    async def get_grn_record(self, grn_id: UUID) -> GRNRecord:
        """Get a GRN record by ID."""
        grn = await self.repo.get_with_po(grn_id)
        if not grn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GRN record not found",
            )
        return grn
    
    async def get_grn_records_by_po(
        self,
        po_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[GRNRecord], int]:
        """Get GRN records for a purchase order."""
        records = await self.repo.get_by_po(po_id, skip, limit)
        total = await self.repo.count(po_id=po_id)
        return records, total
    
    async def get_grn_records_by_date_range(
        self,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[GRNRecord], int]:
        """Get GRN records within a date range."""
        records = await self.repo.get_by_date_range(start_date, end_date, skip, limit)
        # Count is approximate for date range queries
        total = len(records)
        return records, total
    
    async def get_summary(
        self,
        po_ids: Optional[list[UUID]] = None,
    ) -> GRNSummary:
        """Get GRN summary."""
        summary = await self.repo.get_summary(po_ids)
        return GRNSummary(
            total_records=summary["total_records"],
            total_received_value=summary["total_received_value"],
            by_month=summary["by_month"],
        )
    
    async def update_grn_record(
        self,
        grn_id: UUID,
        data: GRNRecordUpdate,
    ) -> GRNRecord:
        """Update a GRN record."""
        grn = await self.repo.get_by_id(grn_id)
        if not grn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GRN record not found",
            )
        
        update_data = data.model_dump(exclude_unset=True)
        updated_grn = await self.repo.update(grn_id, **update_data)
        
        return updated_grn
    
    async def delete_grn_record(self, grn_id: UUID) -> bool:
        """Delete a GRN record."""
        deleted = await self.repo.delete(grn_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GRN record not found",
            )
        return True
    
    async def get_fulfillment_status(self, po_id: UUID) -> dict:
        """Get fulfillment status for a PO."""
        po = await self.po_repo.get_by_id(po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found",
            )
        
        total_received = await self.repo.get_total_received_for_po(po_id)
        
        return {
            "po_id": po_id,
            "po_value": po.po_value,
            "total_received": total_received,
            "remaining": po.po_value - total_received,
            "fulfillment_percentage": (
                (total_received / po.po_value * 100) if po.po_value > 0 else Decimal("0.00")
            ),
        }

"""Range Intent service - business logic for range intents."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workflow_guard import WorkflowGuard
from app.models.range_intent import RangeIntent
from app.models.season import SeasonStatus
from app.repositories.range_intent_repo import RangeIntentRepository
from app.schemas.range_intent import RangeIntentCreate, RangeIntentUpdate
from app.services.audit_service import AuditService


class RangeIntentService:
    """Service for range intent business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RangeIntentRepository(session)
        self.guard = WorkflowGuard(session)
        self.audit = AuditService(session)
    
    async def create_range_intent(self, data: RangeIntentCreate) -> RangeIntent:
        """Create a new range intent."""
        await self.guard.can_upload_range(data.season_id)
        
        # Check for duplicate
        existing = await self.repo.get_by_season_and_category(
            data.season_id,
            data.category_id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Range intent already exists for this season/category combination",
            )
        
        intent = await self.repo.create(
            season_id=data.season_id,
            category_id=data.category_id,
            core_percent=data.core_percent,
            fashion_percent=data.fashion_percent,
            price_band_mix=data.price_band_mix,
            uploaded_by=data.uploaded_by,
        )
        
        return intent
    
    async def bulk_create_range_intents(
        self,
        intents: list[RangeIntentCreate],
    ) -> list[RangeIntent]:
        """Bulk create or update range intents."""
        if not intents:
            return []
        
        await self.guard.can_upload_range(intents[0].season_id)
        
        created_intents = []
        for intent_data in intents:
            intent = await self.repo.upsert(
                season_id=intent_data.season_id,
                category_id=intent_data.category_id,
                core_percent=intent_data.core_percent,
                fashion_percent=intent_data.fashion_percent,
                price_band_mix=intent_data.price_band_mix,
                uploaded_by=intent_data.uploaded_by,
            )
            created_intents.append(intent)
        
        # Update workflow
        await self.guard.update_workflow_step(
            intents[0].season_id,
            "range_uploaded",
            SeasonStatus.RANGE_UPLOADED,
        )
        
        # Audit log the bulk upload
        await self.audit.log_upload(
            entity_type="RangeIntent",
            entity_id=intents[0].season_id,
            user_id=intents[0].uploaded_by,
            record_count=len(created_intents),
            description=f"Bulk uploaded {len(created_intents)} range intents",
            season_id=intents[0].season_id,
        )
        
        return created_intents
    
    async def get_range_intent(self, intent_id: UUID) -> RangeIntent:
        """Get a range intent by ID."""
        intent = await self.repo.get_with_details(intent_id)
        if not intent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Range intent not found",
            )
        return intent
    
    async def get_range_intents_by_season(
        self,
        season_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[RangeIntent], int]:
        """Get range intents for a season."""
        intents = await self.repo.get_by_season(season_id, skip, limit)
        total = await self.repo.count(season_id=season_id)
        return intents, total
    
    async def update_range_intent(
        self,
        intent_id: UUID,
        data: RangeIntentUpdate,
        user_id: Optional[UUID] = None,
    ) -> RangeIntent:
        """Update a range intent."""
        intent = await self.repo.get_by_id(intent_id)
        if not intent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Range intent not found",
            )
        
        # Check range intent is mutable (not locked AND workflow has not progressed past range upload)
        await self.guard.check_range_is_mutable(intent.season_id)
        
        # Capture old data for audit
        old_data = {
            "core_percent": float(intent.core_percent) if intent.core_percent else None,
            "fashion_percent": float(intent.fashion_percent) if intent.fashion_percent else None,
        }
        
        update_data = data.model_dump(exclude_unset=True)
        updated_intent = await self.repo.update(intent_id, **update_data)
        
        # Audit log the update
        await self.audit.log_update(
            entity_type="RangeIntent",
            entity_id=intent_id,
            user_id=user_id,
            old_data=old_data,
            new_data=update_data,
            season_id=intent.season_id,
        )
        
        return updated_intent
    
    async def delete_range_intent(self, intent_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete a range intent."""
        intent = await self.repo.get_by_id(intent_id)
        if not intent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Range intent not found",
            )
        
        # Check range intent is mutable (not locked AND workflow has not progressed past range upload)
        await self.guard.check_range_is_mutable(intent.season_id)
        
        # Capture old data for audit
        old_data = {
            "id": str(intent.id),
            "season_id": str(intent.season_id),
            "category_id": str(intent.category_id) if intent.category_id else None,
        }
        
        result = await self.repo.delete(intent_id)
        
        # Audit log the deletion
        await self.audit.log_delete(
            entity_type="RangeIntent",
            entity_id=intent_id,
            user_id=user_id,
            old_data=old_data,
            season_id=intent.season_id,
        )
        
        return result

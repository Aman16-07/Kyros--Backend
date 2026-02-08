"""Season service - business logic for seasons."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workflow_guard import WorkflowGuard
from app.models.season import Season, SeasonStatus
from app.models.workflow import SeasonWorkflow
from app.repositories.season_repo import SeasonRepository, WorkflowRepository
from app.schemas.season import SeasonCreate, SeasonUpdate
from app.services.audit_service import AuditService


class SeasonService:
    """Service for season business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SeasonRepository(session)
        self.workflow_repo = WorkflowRepository(session)
        self.guard = WorkflowGuard(session)
        self.audit = AuditService(session)
    
    async def create_season(self, data: SeasonCreate) -> Season:
        """Create a new season with workflow."""
        # Validate dates
        if data.end_date <= data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date",
            )
        
        # Create season with workflow
        season = await self.repo.create_with_workflow(
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            created_by=data.created_by,
            company_id=data.company_id,
            status=SeasonStatus.CREATED,
        )
        
        # Audit log the creation
        await self.audit.log_create(
            entity_type="Season",
            entity_id=season.id,
            user_id=data.created_by,
            new_data={
                "name": data.name,
                "start_date": data.start_date.isoformat(),
                "end_date": data.end_date.isoformat(),
                "status": SeasonStatus.CREATED.value,
            },
            description=f"Created season: {data.name}",
            season_id=season.id,
        )
        
        return season
    
    async def get_season(self, season_id: UUID) -> Optional[Season]:
        """Get a season by ID."""
        season = await self.repo.get_with_workflow(season_id)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )
        return season
    
    async def get_seasons(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[SeasonStatus] = None,
    ) -> tuple[list[Season], int]:
        """Get all seasons with optional filtering."""
        if status_filter:
            seasons = await self.repo.get_by_status(status_filter, skip, limit)
            total = await self.repo.count(status=status_filter)
        else:
            seasons = await self.repo.get_all_with_workflow(skip, limit)
            total = await self.repo.count()
        
        return seasons, total
    
    async def get_seasons_by_company(
        self,
        company_id: Optional[UUID],
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[SeasonStatus] = None,
    ) -> tuple[list[Season], int]:
        """Get all seasons for a specific company."""
        seasons = await self.repo.get_by_company(company_id, skip, limit, status_filter)
        total = await self.repo.count_by_company(company_id, status_filter)
        return seasons, total
    
    async def update_season(
        self,
        season_id: UUID,
        data: SeasonUpdate,
        user_id: Optional[UUID] = None,
    ) -> Season:
        """Update a season."""
        # Check not locked
        await self.guard.check_not_locked(season_id)
        
        # Get old data for audit
        old_season = await self.repo.get_by_id(season_id)
        if not old_season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )
        
        old_data = {
            "name": old_season.name,
            "start_date": old_season.start_date.isoformat() if old_season.start_date else None,
            "end_date": old_season.end_date.isoformat() if old_season.end_date else None,
        }
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Don't allow direct status updates through this method
        if "status" in update_data:
            del update_data["status"]
        
        season = await self.repo.update(season_id, **update_data)
        
        # Audit log the update
        await self.audit.log_update(
            entity_type="Season",
            entity_id=season_id,
            user_id=user_id,
            old_data=old_data,
            new_data=update_data,
            description=f"Updated season: {season.name}",
            season_id=season_id,
        )
        
        return season
    
    async def delete_season(self, season_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete a season."""
        # Check not locked
        await self.guard.check_not_locked(season_id)
        
        # Get season data for audit before deleting
        season = await self.repo.get_by_id(season_id)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )
        
        old_data = {
            "id": str(season_id),
            "name": season.name,
            "status": season.status.value if season.status else None,
        }
        
        deleted = await self.repo.delete(season_id)
        
        # Audit log the deletion
        await self.audit.log_delete(
            entity_type="Season",
            entity_id=season_id,
            user_id=user_id,
            old_data=old_data,
            description=f"Deleted season: {season.name}",
            season_id=season_id,
        )
        
        return True
    
    async def mark_locations_defined(self, season_id: UUID, user_id: Optional[UUID] = None) -> SeasonWorkflow:
        """Mark locations as defined for a season."""
        await self.guard.check_season_exists(season_id)
        await self.guard.check_not_locked(season_id)
        
        result = await self.guard.update_workflow_step(
            season_id,
            "locations_defined",
            SeasonStatus.LOCATIONS_DEFINED,
        )
        
        # Audit log the workflow transition
        await self.audit.log_workflow_transition(
            season_id=season_id,
            user_id=user_id,
            old_status=SeasonStatus.CREATED.value,
            new_status=SeasonStatus.LOCATIONS_DEFINED.value,
            description="Locations defined for season",
        )
        
        return result
    
    async def lock_season(self, season_id: UUID, user_id: Optional[UUID] = None) -> SeasonWorkflow:
        """Lock a season."""
        await self.guard.can_lock_season(season_id)
        
        result = await self.guard.update_workflow_step(
            season_id,
            "locked",
            SeasonStatus.LOCKED,
        )
        
        # Audit log the lock action
        await self.audit.log_lock(
            season_id=season_id,
            user_id=user_id,
            description="Season locked for read-only access",
        )
        
        return result
    
    async def get_workflow(self, season_id: UUID) -> SeasonWorkflow:
        """Get workflow status for a season."""
        workflow = await self.workflow_repo.get_by_season_id(season_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found for this season",
            )
        return workflow

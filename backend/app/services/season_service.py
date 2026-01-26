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


class SeasonService:
    """Service for season business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SeasonRepository(session)
        self.workflow_repo = WorkflowRepository(session)
        self.guard = WorkflowGuard(session)
    
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
            status=SeasonStatus.CREATED,
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
    
    async def update_season(
        self,
        season_id: UUID,
        data: SeasonUpdate,
    ) -> Season:
        """Update a season."""
        # Check not locked
        await self.guard.check_not_locked(season_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Don't allow direct status updates through this method
        if "status" in update_data:
            del update_data["status"]
        
        season = await self.repo.update(season_id, **update_data)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )
        
        return season
    
    async def delete_season(self, season_id: UUID) -> bool:
        """Delete a season."""
        # Check not locked
        await self.guard.check_not_locked(season_id)
        
        deleted = await self.repo.delete(season_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )
        
        return True
    
    async def mark_locations_defined(self, season_id: UUID) -> SeasonWorkflow:
        """Mark locations as defined for a season."""
        await self.guard.check_season_exists(season_id)
        await self.guard.check_not_locked(season_id)
        
        return await self.guard.update_workflow_step(
            season_id,
            "locations_defined",
            SeasonStatus.LOCATIONS_DEFINED,
        )
    
    async def lock_season(self, season_id: UUID) -> SeasonWorkflow:
        """Lock a season."""
        await self.guard.can_lock_season(season_id)
        
        return await self.guard.update_workflow_step(
            season_id,
            "locked",
            SeasonStatus.LOCKED,
        )
    
    async def get_workflow(self, season_id: UUID) -> SeasonWorkflow:
        """Get workflow status for a season."""
        workflow = await self.workflow_repo.get_by_season_id(season_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found for this season",
            )
        return workflow

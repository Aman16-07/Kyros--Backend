"""Workflow enforcement utilities."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.season import SeasonStatus
from app.models.workflow import SeasonWorkflow
from app.repositories.season_repo import SeasonRepository, WorkflowRepository


class WorkflowGuard:
    """Guard for enforcing workflow state transitions."""
    
    # Define valid transitions
    WORKFLOW_TRANSITIONS = {
        SeasonStatus.CREATED: [SeasonStatus.LOCATIONS_DEFINED],
        SeasonStatus.LOCATIONS_DEFINED: [SeasonStatus.PLAN_UPLOADED],
        SeasonStatus.PLAN_UPLOADED: [SeasonStatus.OTB_UPLOADED],
        SeasonStatus.OTB_UPLOADED: [SeasonStatus.RANGE_UPLOADED],
        SeasonStatus.RANGE_UPLOADED: [SeasonStatus.LOCKED],
        SeasonStatus.LOCKED: [],  # No transitions from locked
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.season_repo = SeasonRepository(session)
        self.workflow_repo = WorkflowRepository(session)
    
    async def get_workflow(self, season_id: UUID) -> Optional[SeasonWorkflow]:
        """Get workflow for a season."""
        return await self.workflow_repo.get_by_season_id(season_id)
    
    async def check_season_exists(self, season_id: UUID) -> None:
        """Check if season exists."""
        season = await self.season_repo.get_by_id(season_id)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Season {season_id} not found",
            )
    
    async def check_not_locked(self, season_id: UUID) -> None:
        """Check if season is not locked."""
        season = await self.season_repo.get_by_id(season_id)
        if season and season.status == SeasonStatus.LOCKED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Season is locked and cannot be modified",
            )
    
    async def check_locations_defined(self, season_id: UUID) -> None:
        """Check if locations are defined for the season."""
        workflow = await self.get_workflow(season_id)
        if not workflow or not workflow.locations_defined:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Locations must be defined before this operation",
            )
    
    async def check_plan_uploaded(self, season_id: UUID) -> None:
        """Check if season plan is uploaded."""
        workflow = await self.get_workflow(season_id)
        if not workflow or not workflow.plan_uploaded:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Season plan must be uploaded before this operation",
            )
    
    async def check_otb_uploaded(self, season_id: UUID) -> None:
        """Check if OTB is uploaded."""
        workflow = await self.get_workflow(season_id)
        if not workflow or not workflow.otb_uploaded:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTB plan must be uploaded before this operation",
            )
    
    async def check_range_uploaded(self, season_id: UUID) -> None:
        """Check if range intent is uploaded."""
        workflow = await self.get_workflow(season_id)
        if not workflow or not workflow.range_uploaded:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Range intent must be uploaded before this operation",
            )
    
    async def can_upload_plan(self, season_id: UUID) -> bool:
        """Check if season plan can be uploaded."""
        await self.check_season_exists(season_id)
        await self.check_not_locked(season_id)
        await self.check_locations_defined(season_id)
        return True
    
    async def can_upload_otb(self, season_id: UUID) -> bool:
        """Check if OTB can be uploaded."""
        await self.check_season_exists(season_id)
        await self.check_not_locked(season_id)
        await self.check_plan_uploaded(season_id)
        return True
    
    async def can_upload_range(self, season_id: UUID) -> bool:
        """Check if range intent can be uploaded."""
        await self.check_season_exists(season_id)
        await self.check_not_locked(season_id)
        await self.check_otb_uploaded(season_id)
        return True
    
    async def can_lock_season(self, season_id: UUID) -> bool:
        """Check if season can be locked."""
        await self.check_season_exists(season_id)
        await self.check_range_uploaded(season_id)
        
        workflow = await self.get_workflow(season_id)
        if workflow and workflow.locked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Season is already locked",
            )
        return True
    
    async def update_workflow_step(
        self,
        season_id: UUID,
        step: str,
        new_status: SeasonStatus,
    ) -> SeasonWorkflow:
        """Update workflow step and season status."""
        # Update workflow
        workflow = await self.workflow_repo.update_workflow_step(
            season_id, step, True
        )
        
        # Update season status
        await self.season_repo.update_status(season_id, new_status)
        
        return workflow

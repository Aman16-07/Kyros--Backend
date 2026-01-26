"""Season repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.season import Season, SeasonStatus
from app.models.workflow import SeasonWorkflow
from app.repositories.base_repo import BaseRepository


class SeasonRepository(BaseRepository[Season]):
    """Repository for Season model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Season, session)
    
    async def get_with_workflow(self, season_id: UUID) -> Optional[Season]:
        """Get season with workflow status."""
        result = await self.session.execute(
            select(Season)
            .options(selectinload(Season.workflow))
            .where(Season.id == season_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_with_workflow(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Season]:
        """Get all seasons with workflow status."""
        result = await self.session.execute(
            select(Season)
            .options(selectinload(Season.workflow))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_status(
        self,
        status: SeasonStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Season]:
        """Get seasons by status."""
        result = await self.session.execute(
            select(Season)
            .where(Season.status == status)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_active_seasons(self) -> list[Season]:
        """Get seasons that are not locked."""
        result = await self.session.execute(
            select(Season)
            .where(Season.status != SeasonStatus.LOCKED)
            .options(selectinload(Season.workflow))
        )
        return list(result.scalars().all())
    
    async def create_with_workflow(self, **kwargs) -> Season:
        """Create season with initial workflow state."""
        season = await self.create(**kwargs)
        
        workflow = SeasonWorkflow(
            season_id=season.id,
            locations_defined=False,
            plan_uploaded=False,
            otb_uploaded=False,
            range_uploaded=False,
            locked=False,
        )
        self.session.add(workflow)
        await self.session.flush()
        await self.session.refresh(season)
        
        return season
    
    async def update_status(
        self,
        season_id: UUID,
        status: SeasonStatus,
    ) -> Optional[Season]:
        """Update season status."""
        return await self.update(season_id, status=status)


class WorkflowRepository(BaseRepository[SeasonWorkflow]):
    """Repository for SeasonWorkflow model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(SeasonWorkflow, session)
    
    async def get_by_season_id(self, season_id: UUID) -> Optional[SeasonWorkflow]:
        """Get workflow by season ID."""
        result = await self.session.execute(
            select(SeasonWorkflow).where(SeasonWorkflow.season_id == season_id)
        )
        return result.scalar_one_or_none()
    
    async def update_workflow_step(
        self,
        season_id: UUID,
        step: str,
        value: bool = True,
    ) -> Optional[SeasonWorkflow]:
        """Update a specific workflow step."""
        workflow = await self.get_by_season_id(season_id)
        if workflow is None:
            return None
        
        if hasattr(workflow, step):
            setattr(workflow, step, value)
            await self.session.flush()
            await self.session.refresh(workflow)
        
        return workflow
    
    async def lock_season(self, season_id: UUID) -> Optional[SeasonWorkflow]:
        """Lock a season's workflow."""
        return await self.update_workflow_step(season_id, "locked", True)

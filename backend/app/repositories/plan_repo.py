"""Season Plan repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.season_plan import SeasonPlan
from app.repositories.base_repo import BaseRepository


class SeasonPlanRepository(BaseRepository[SeasonPlan]):
    """Repository for SeasonPlan model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(SeasonPlan, session)
    
    async def get_by_season(
        self,
        season_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SeasonPlan]:
        """Get plans by season."""
        result = await self.session.execute(
            select(SeasonPlan)
            .where(SeasonPlan.season_id == season_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_season_location_category(
        self,
        season_id: UUID,
        location_id: UUID,
        category_id: UUID,
    ) -> list[SeasonPlan]:
        """Get plans by season, location, and category."""
        result = await self.session.execute(
            select(SeasonPlan)
            .where(
                SeasonPlan.season_id == season_id,
                SeasonPlan.location_id == location_id,
                SeasonPlan.category_id == category_id,
            )
            .order_by(SeasonPlan.version.desc())
        )
        return list(result.scalars().all())
    
    async def get_latest_version(
        self,
        season_id: UUID,
        location_id: UUID,
        category_id: UUID,
    ) -> Optional[SeasonPlan]:
        """Get the latest version of a plan."""
        result = await self.session.execute(
            select(SeasonPlan)
            .where(
                SeasonPlan.season_id == season_id,
                SeasonPlan.location_id == location_id,
                SeasonPlan.category_id == category_id,
            )
            .order_by(SeasonPlan.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_next_version(
        self,
        season_id: UUID,
        location_id: UUID,
        category_id: UUID,
    ) -> int:
        """Get the next version number for a plan."""
        result = await self.session.execute(
            select(func.max(SeasonPlan.version))
            .where(
                SeasonPlan.season_id == season_id,
                SeasonPlan.location_id == location_id,
                SeasonPlan.category_id == category_id,
            )
        )
        max_version = result.scalar() or 0
        return max_version + 1
    
    async def get_approved_plans(
        self,
        season_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SeasonPlan]:
        """Get approved plans for a season."""
        result = await self.session.execute(
            select(SeasonPlan)
            .where(
                SeasonPlan.season_id == season_id,
                SeasonPlan.approved == True,
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def approve_plans(self, plan_ids: list[UUID], approved: bool = True) -> int:
        """Approve or reject multiple plans."""
        count = 0
        for plan_id in plan_ids:
            plan = await self.get_by_id(plan_id)
            if plan:
                plan.approved = approved
                count += 1
        await self.session.flush()
        return count
    
    async def get_with_details(self, plan_id: UUID) -> Optional[SeasonPlan]:
        """Get plan with related entities."""
        result = await self.session.execute(
            select(SeasonPlan)
            .options(
                selectinload(SeasonPlan.season),
                selectinload(SeasonPlan.location),
                selectinload(SeasonPlan.category),
            )
            .where(SeasonPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

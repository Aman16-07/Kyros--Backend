"""OTB Plan repository."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.otb_plan import OTBPlan
from app.repositories.base_repo import BaseRepository


class OTBPlanRepository(BaseRepository[OTBPlan]):
    """Repository for OTBPlan model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(OTBPlan, session)
    
    async def get_by_season(
        self,
        season_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OTBPlan]:
        """Get OTB plans by season."""
        result = await self.session.execute(
            select(OTBPlan)
            .where(OTBPlan.season_id == season_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_season_and_month(
        self,
        season_id: UUID,
        month: date,
    ) -> list[OTBPlan]:
        """Get OTB plans by season and month."""
        result = await self.session.execute(
            select(OTBPlan)
            .where(
                OTBPlan.season_id == season_id,
                OTBPlan.month == month,
            )
        )
        return list(result.scalars().all())
    
    async def get_by_composite_key(
        self,
        season_id: UUID,
        location_id: UUID,
        category_id: UUID,
        month: date,
    ) -> Optional[OTBPlan]:
        """Get OTB plan by composite unique key."""
        result = await self.session.execute(
            select(OTBPlan)
            .where(
                OTBPlan.season_id == season_id,
                OTBPlan.location_id == location_id,
                OTBPlan.category_id == category_id,
                OTBPlan.month == month,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_total_spend_by_month(
        self,
        season_id: UUID,
    ) -> list[dict]:
        """Get total spend limit by month for a season."""
        result = await self.session.execute(
            select(
                OTBPlan.month,
                func.sum(OTBPlan.approved_spend_limit).label("total"),
                func.count(func.distinct(OTBPlan.location_id)).label("location_count"),
                func.count(func.distinct(OTBPlan.category_id)).label("category_count"),
            )
            .where(OTBPlan.season_id == season_id)
            .group_by(OTBPlan.month)
            .order_by(OTBPlan.month)
        )
        return [
            {
                "month": row.month,
                "total_spend_limit": row.total or Decimal("0.00"),
                "location_count": row.location_count,
                "category_count": row.category_count,
            }
            for row in result.all()
        ]
    
    async def get_with_details(self, plan_id: UUID) -> Optional[OTBPlan]:
        """Get OTB plan with related entities."""
        result = await self.session.execute(
            select(OTBPlan)
            .options(
                selectinload(OTBPlan.season),
                selectinload(OTBPlan.location),
                selectinload(OTBPlan.category),
            )
            .where(OTBPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

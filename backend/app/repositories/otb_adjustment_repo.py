"""OTB Adjustment repository - data access for OTB rebalancing."""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.otb_adjustment import AdjustmentStatus, OTBAdjustment
from app.repositories.base_repo import BaseRepository


class OTBAdjustmentRepository(BaseRepository[OTBAdjustment]):
    def __init__(self, session: AsyncSession):
        super().__init__(OTBAdjustment, session)

    async def get_by_season(
        self, season_id: UUID, skip: int = 0, limit: int = 100,
    ) -> list[OTBAdjustment]:
        result = await self.session.execute(
            select(OTBAdjustment)
            .where(OTBAdjustment.season_id == season_id)
            .order_by(OTBAdjustment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_season_and_status(
        self, season_id: UUID, status: AdjustmentStatus,
    ) -> list[OTBAdjustment]:
        result = await self.session.execute(
            select(OTBAdjustment)
            .where(
                OTBAdjustment.season_id == season_id,
                OTBAdjustment.status == status,
            )
            .order_by(OTBAdjustment.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_pending(self, season_id: UUID) -> list[OTBAdjustment]:
        return await self.get_by_season_and_status(season_id, AdjustmentStatus.PENDING)

    async def get_with_details(self, adjustment_id: UUID) -> Optional[OTBAdjustment]:
        result = await self.session.execute(
            select(OTBAdjustment)
            .options(
                selectinload(OTBAdjustment.season),
                selectinload(OTBAdjustment.from_category),
                selectinload(OTBAdjustment.to_category),
                selectinload(OTBAdjustment.approver),
                selectinload(OTBAdjustment.creator),
            )
            .where(OTBAdjustment.id == adjustment_id)
        )
        return result.scalar_one_or_none()

    async def count_by_season(self, season_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(OTBAdjustment)
            .where(OTBAdjustment.season_id == season_id)
        )
        return result.scalar() or 0

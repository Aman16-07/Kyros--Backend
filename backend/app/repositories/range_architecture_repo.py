"""Range Architecture repository - data access for range planning."""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.range_architecture import RangeArchitecture, RangeStatus
from app.repositories.base_repo import BaseRepository


class RangeArchitectureRepository(BaseRepository[RangeArchitecture]):
    def __init__(self, session: AsyncSession):
        super().__init__(RangeArchitecture, session)

    async def get_by_season(
        self, season_id: UUID, skip: int = 0, limit: int = 100,
    ) -> list[RangeArchitecture]:
        result = await self.session.execute(
            select(RangeArchitecture)
            .where(RangeArchitecture.season_id == season_id)
            .order_by(RangeArchitecture.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_season_and_category(
        self, season_id: UUID, category_id: UUID,
    ) -> list[RangeArchitecture]:
        result = await self.session.execute(
            select(RangeArchitecture)
            .where(
                RangeArchitecture.season_id == season_id,
                RangeArchitecture.category_id == category_id,
            )
            .order_by(RangeArchitecture.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_season_and_status(
        self, season_id: UUID, status: RangeStatus,
    ) -> list[RangeArchitecture]:
        result = await self.session.execute(
            select(RangeArchitecture)
            .where(
                RangeArchitecture.season_id == season_id,
                RangeArchitecture.status == status,
            )
            .order_by(RangeArchitecture.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_details(self, arch_id: UUID) -> Optional[RangeArchitecture]:
        result = await self.session.execute(
            select(RangeArchitecture)
            .options(
                selectinload(RangeArchitecture.season),
                selectinload(RangeArchitecture.category),
                selectinload(RangeArchitecture.submitter),
                selectinload(RangeArchitecture.reviewer),
                selectinload(RangeArchitecture.creator),
            )
            .where(RangeArchitecture.id == arch_id)
        )
        return result.scalar_one_or_none()

    async def count_by_season(self, season_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(RangeArchitecture)
            .where(RangeArchitecture.season_id == season_id)
        )
        return result.scalar() or 0

    async def get_for_comparison(self, season_id: UUID) -> list[RangeArchitecture]:
        """Get all range architectures for a season, loaded with category details."""
        result = await self.session.execute(
            select(RangeArchitecture)
            .options(selectinload(RangeArchitecture.category))
            .where(RangeArchitecture.season_id == season_id)
            .order_by(RangeArchitecture.category_id, RangeArchitecture.price_band)
        )
        return list(result.scalars().all())

    async def bulk_update_status(
        self, ids: list[UUID], status: RangeStatus, **kwargs,
    ) -> list[RangeArchitecture]:
        """Update status for multiple range architectures."""
        updated = []
        for arch_id in ids:
            arch = await self.get_by_id(arch_id)
            if arch:
                arch.status = status
                for key, value in kwargs.items():
                    if hasattr(arch, key) and value is not None:
                        setattr(arch, key, value)
                await self.session.flush()
                await self.session.refresh(arch)
                updated.append(arch)
        return updated

"""Range Intent repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.range_intent import RangeIntent
from app.repositories.base_repo import BaseRepository


class RangeIntentRepository(BaseRepository[RangeIntent]):
    """Repository for RangeIntent model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(RangeIntent, session)
    
    async def get_by_season(
        self,
        season_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RangeIntent]:
        """Get range intents by season."""
        result = await self.session.execute(
            select(RangeIntent)
            .where(RangeIntent.season_id == season_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_season_and_category(
        self,
        season_id: UUID,
        category_id: UUID,
    ) -> Optional[RangeIntent]:
        """Get range intent by season and category."""
        result = await self.session.execute(
            select(RangeIntent)
            .where(
                RangeIntent.season_id == season_id,
                RangeIntent.category_id == category_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_with_details(self, intent_id: UUID) -> Optional[RangeIntent]:
        """Get range intent with related entities."""
        result = await self.session.execute(
            select(RangeIntent)
            .options(
                selectinload(RangeIntent.season),
                selectinload(RangeIntent.category),
            )
            .where(RangeIntent.id == intent_id)
        )
        return result.scalar_one_or_none()
    
    async def upsert(
        self,
        season_id: UUID,
        category_id: UUID,
        **kwargs,
    ) -> RangeIntent:
        """Insert or update range intent by season and category."""
        existing = await self.get_by_season_and_category(season_id, category_id)
        
        if existing:
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        
        return await self.create(
            season_id=season_id,
            category_id=category_id,
            **kwargs,
        )

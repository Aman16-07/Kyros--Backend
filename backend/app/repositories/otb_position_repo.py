"""OTB Position repository - data access for dynamic OTB tracking."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.otb_position import OTBPosition
from app.repositories.base_repo import BaseRepository


class OTBPositionRepository(BaseRepository[OTBPosition]):
    def __init__(self, session: AsyncSession):
        super().__init__(OTBPosition, session)

    async def get_by_season(
        self, season_id: UUID, skip: int = 0, limit: int = 100,
    ) -> list[OTBPosition]:
        result = await self.session.execute(
            select(OTBPosition)
            .where(OTBPosition.season_id == season_id)
            .order_by(OTBPosition.month)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_season_and_category(
        self, season_id: UUID, category_id: UUID,
    ) -> list[OTBPosition]:
        result = await self.session.execute(
            select(OTBPosition)
            .where(
                OTBPosition.season_id == season_id,
                OTBPosition.category_id == category_id,
            )
            .order_by(OTBPosition.month)
        )
        return list(result.scalars().all())

    async def get_by_composite_key(
        self, season_id: UUID, category_id: Optional[UUID], month: date,
    ) -> Optional[OTBPosition]:
        query = select(OTBPosition).where(
            OTBPosition.season_id == season_id,
            OTBPosition.month == month,
        )
        if category_id is not None:
            query = query.where(OTBPosition.category_id == category_id)
        else:
            query = query.where(OTBPosition.category_id.is_(None))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_category_summary(self, season_id: UUID) -> list[dict]:
        """Aggregate OTB positions by category for a season."""
        result = await self.session.execute(
            select(
                OTBPosition.category_id,
                func.sum(OTBPosition.planned_otb).label("total_planned"),
                func.sum(OTBPosition.consumed_otb).label("total_consumed"),
                func.sum(OTBPosition.available_otb).label("total_available"),
            )
            .where(OTBPosition.season_id == season_id)
            .group_by(OTBPosition.category_id)
        )
        return [
            {
                "category_id": row.category_id,
                "total_planned": row.total_planned or Decimal("0.00"),
                "total_consumed": row.total_consumed or Decimal("0.00"),
                "total_available": row.total_available or Decimal("0.00"),
            }
            for row in result.all()
        ]

    async def get_month_summary(self, season_id: UUID) -> list[dict]:
        """Aggregate OTB positions by month for a season."""
        result = await self.session.execute(
            select(
                OTBPosition.month,
                func.sum(OTBPosition.planned_otb).label("planned_otb"),
                func.sum(OTBPosition.consumed_otb).label("consumed_otb"),
                func.sum(OTBPosition.available_otb).label("available_otb"),
            )
            .where(OTBPosition.season_id == season_id)
            .group_by(OTBPosition.month)
            .order_by(OTBPosition.month)
        )
        return [
            {
                "month": row.month,
                "planned_otb": row.planned_otb or Decimal("0.00"),
                "consumed_otb": row.consumed_otb or Decimal("0.00"),
                "available_otb": row.available_otb or Decimal("0.00"),
            }
            for row in result.all()
        ]

    async def get_season_totals(self, season_id: UUID) -> dict:
        """Get aggregate totals for the whole season."""
        result = await self.session.execute(
            select(
                func.sum(OTBPosition.planned_otb).label("total_planned"),
                func.sum(OTBPosition.consumed_otb).label("total_consumed"),
                func.sum(OTBPosition.available_otb).label("total_available"),
            )
            .where(OTBPosition.season_id == season_id)
        )
        row = result.one()
        return {
            "total_planned": row.total_planned or Decimal("0.00"),
            "total_consumed": row.total_consumed or Decimal("0.00"),
            "total_available": row.total_available or Decimal("0.00"),
        }

    async def get_with_details(self, position_id: UUID) -> Optional[OTBPosition]:
        result = await self.session.execute(
            select(OTBPosition)
            .options(
                selectinload(OTBPosition.season),
                selectinload(OTBPosition.category),
            )
            .where(OTBPosition.id == position_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        season_id: UUID,
        category_id: Optional[UUID],
        month: date,
        planned_otb: Decimal,
        consumed_otb: Decimal,
        available_otb: Decimal,
    ) -> OTBPosition:
        """Create or update an OTB position."""
        existing = await self.get_by_composite_key(season_id, category_id, month)
        if existing:
            existing.planned_otb = planned_otb
            existing.consumed_otb = consumed_otb
            existing.available_otb = available_otb
            from datetime import datetime, timezone
            existing.last_calculated = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        else:
            from datetime import datetime, timezone
            return await self.create(
                season_id=season_id,
                category_id=category_id,
                month=month.replace(day=1),
                planned_otb=planned_otb,
                consumed_otb=consumed_otb,
                available_otb=available_otb,
                last_calculated=datetime.now(timezone.utc),
            )

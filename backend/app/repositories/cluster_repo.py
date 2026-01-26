"""Cluster repository."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cluster import Cluster
from app.repositories.base_repo import BaseRepository


class ClusterRepository(BaseRepository[Cluster]):
    """Repository for Cluster model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Cluster, session)
    
    async def get_by_name(self, name: str) -> Optional[Cluster]:
        """Get cluster by name."""
        result = await self.session.execute(
            select(Cluster).where(Cluster.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_with_locations(self, cluster_id) -> Optional[Cluster]:
        """Get cluster with its locations."""
        result = await self.session.execute(
            select(Cluster)
            .options(selectinload(Cluster.locations))
            .where(Cluster.id == cluster_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_with_locations(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Cluster]:
        """Get all clusters with their locations."""
        result = await self.session.execute(
            select(Cluster)
            .options(selectinload(Cluster.locations))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

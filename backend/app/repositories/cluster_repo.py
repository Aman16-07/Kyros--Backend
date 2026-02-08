"""Cluster repository."""

import uuid as uuid_module
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cluster import Cluster
from app.repositories.base_repo import BaseRepository


def generate_cluster_code() -> str:
    """Generate a unique cluster code like CLU-A7B3C9D1."""
    short_uuid = uuid_module.uuid4().hex[:8].upper()
    return f"CLU-{short_uuid}"


class ClusterRepository(BaseRepository[Cluster]):
    """Repository for Cluster model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Cluster, session)
    
    async def get_by_code(self, cluster_code: str) -> Optional[Cluster]:
        """Get cluster by cluster_code."""
        result = await self.session.execute(
            select(Cluster).where(Cluster.cluster_code == cluster_code)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Cluster]:
        """Get cluster by name."""
        result = await self.session.execute(
            select(Cluster).where(Cluster.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name_and_company(self, name: str, company_id: Optional[UUID]) -> Optional[Cluster]:
        """Get cluster by name within a specific company."""
        query = select(Cluster).where(Cluster.name == name)
        if company_id:
            query = query.where(Cluster.company_id == company_id)
        else:
            query = query.where(Cluster.company_id.is_(None))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_company(
        self, company_id: Optional[UUID], skip: int = 0, limit: int = 100
    ) -> list[Cluster]:
        """Get all clusters for a specific company.
        
        If company_id is None, returns clusters with NULL company_id only.
        Use get_all() for super admin to see all clusters.
        """
        query = select(Cluster)
        if company_id:
            query = query.where(Cluster.company_id == company_id)
        else:
            # For users without a company, only show clusters without a company
            query = query.where(Cluster.company_id.is_(None))
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_company(self, company_id: Optional[UUID]) -> int:
        """Count clusters for a specific company."""
        query = select(func.count(Cluster.id))
        if company_id:
            query = query.where(Cluster.company_id == company_id)
        else:
            query = query.where(Cluster.company_id.is_(None))
        result = await self.session.execute(query)
        return result.scalar_one()
    
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

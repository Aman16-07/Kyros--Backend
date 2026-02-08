"""Location repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.location import Location, LocationType
from app.repositories.base_repo import BaseRepository


class LocationRepository(BaseRepository[Location]):
    """Repository for Location model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Location, session)
    
    async def get_by_name(self, name: str) -> Optional[Location]:
        """Get location by name."""
        result = await self.session.execute(
            select(Location).where(Location.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name_and_company(
        self, name: str, company_id: Optional[UUID]
    ) -> Optional[Location]:
        """Get location by name within a specific company."""
        query = select(Location).where(Location.name == name)
        if company_id:
            query = query.where(Location.company_id == company_id)
        else:
            query = query.where(Location.company_id.is_(None))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_company(
        self,
        company_id: Optional[UUID],
        location_type: Optional[LocationType] = None,
        cluster_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Location]:
        """Get all locations for a specific company with optional filters."""
        query = select(Location)
        if company_id:
            query = query.where(Location.company_id == company_id)
        else:
            query = query.where(Location.company_id.is_(None))
        if location_type:
            query = query.where(Location.type == location_type)
        if cluster_id:
            query = query.where(Location.cluster_id == cluster_id)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_company(
        self,
        company_id: Optional[UUID],
        location_type: Optional[LocationType] = None,
        cluster_id: Optional[UUID] = None,
    ) -> int:
        """Count locations for a specific company with optional filters."""
        query = select(func.count(Location.id))
        if company_id:
            query = query.where(Location.company_id == company_id)
        else:
            query = query.where(Location.company_id.is_(None))
        if location_type:
            query = query.where(Location.type == location_type)
        if cluster_id:
            query = query.where(Location.cluster_id == cluster_id)
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def get_by_cluster(
        self,
        cluster_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Location]:
        """Get locations by cluster."""
        result = await self.session.execute(
            select(Location)
            .where(Location.cluster_id == cluster_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_type(
        self,
        location_type: LocationType,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Location]:
        """Get locations by type."""
        result = await self.session.execute(
            select(Location)
            .where(Location.type == location_type)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_stores(self, skip: int = 0, limit: int = 100) -> list[Location]:
        """Get all store locations."""
        return await self.get_by_type(LocationType.STORE, skip, limit)
    
    async def get_warehouses(self, skip: int = 0, limit: int = 100) -> list[Location]:
        """Get all warehouse locations."""
        return await self.get_by_type(LocationType.WAREHOUSE, skip, limit)
    
    async def get_with_cluster(self, location_id: UUID) -> Optional[Location]:
        """Get location with cluster details."""
        result = await self.session.execute(
            select(Location)
            .options(selectinload(Location.cluster))
            .where(Location.id == location_id)
        )
        return result.scalar_one_or_none()

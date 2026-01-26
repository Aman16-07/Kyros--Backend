"""Category repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.repositories.base_repo import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for Category model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Category, session)
    
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name."""
        result = await self.session.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_root_categories(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Category]:
        """Get top-level categories (no parent)."""
        result = await self.session.execute(
            select(Category)
            .where(Category.parent_id.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_children(
        self,
        parent_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Category]:
        """Get child categories of a parent."""
        result = await self.session.execute(
            select(Category)
            .where(Category.parent_id == parent_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_with_children(self, category_id: UUID) -> Optional[Category]:
        """Get category with its children."""
        result = await self.session.execute(
            select(Category)
            .options(selectinload(Category.children))
            .where(Category.id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def get_tree(self) -> list[Category]:
        """Get full category tree (root categories with all children loaded)."""
        # Recursive loading - get roots with children
        result = await self.session.execute(
            select(Category)
            .where(Category.parent_id.is_(None))
            .options(selectinload(Category.children, recursion_depth=5))
        )
        return list(result.scalars().all())
    
    async def get_with_parent(self, category_id: UUID) -> Optional[Category]:
        """Get category with its parent."""
        result = await self.session.execute(
            select(Category)
            .options(selectinload(Category.parent))
            .where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

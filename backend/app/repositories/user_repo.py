"""User repository."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_name(self, name: str) -> Optional[User]:
        """Get user by name."""
        result = await self.session.execute(
            select(User).where(User.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_role(
        self,
        role: UserRole,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get users by role."""
        result = await self.session.execute(
            select(User)
            .where(User.role == role)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_admins(self) -> list[User]:
        """Get all admin users."""
        return await self.get_by_role(UserRole.ADMIN)

"""User repository."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def create(
        self,
        name: str,
        email: str,
        password: str,
        role: UserRole = UserRole.VIEWER,
        company_id: Optional[str] = None,
        company_name: Optional[str] = None,
        company_code: Optional[str] = None,
        is_active: bool = True,
    ) -> User:
        """Create a new user with hashed password."""
        user = User(
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=role,
            company_id=company_id,
            company_name=company_name,
            company_code=company_code,
            is_active=is_active,
            is_verified=False,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[User]:
        """Get user by name."""
        result = await self.session.execute(
            select(User).where(User.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_code(
        self,
        company_code: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get users by company code."""
        result = await self.session.execute(
            select(User)
            .where(User.company_code == company_code)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def list_by_company(
        self,
        company_id: str,
    ) -> list[User]:
        """Get all users belonging to a company by company_id."""
        result = await self.session.execute(
            select(User)
            .where(User.company_id == company_id)
        )
        return list(result.scalars().all())
    
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
    
    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get only active users."""
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_admins(self) -> list[User]:
        """Get all admin users."""
        return await self.get_by_role(UserRole.ADMIN)
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Returns the user if email and password match, None otherwise.
        Note: is_active check is done in the login endpoint for better error messages.
        """
        user = await self.get_by_email(email)
        if user is None:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def update_last_login(self, user_id: UUID) -> None:
        """Update the last login timestamp for a user."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )
        await self.session.flush()
    
    async def update_password(self, user_id: UUID, new_password: str) -> None:
        """Update user's password."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                password_hash=hash_password(new_password),
                password_reset_token=None,
                password_reset_expires=None,
            )
        )
        await self.session.flush()
    
    async def set_password_reset_token(
        self,
        user_id: UUID,
        token: str,
        expires: datetime,
    ) -> None:
        """Set password reset token for a user."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                password_reset_token=token,
                password_reset_expires=expires,
            )
        )
        await self.session.flush()
    
    async def get_by_reset_token(self, token: str) -> Optional[User]:
        """Get user by password reset token if not expired."""
        result = await self.session.execute(
            select(User).where(
                User.password_reset_token == token,
                User.password_reset_expires > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()
    
    async def set_refresh_token(self, user_id: UUID, token_hash: str) -> None:
        """Store hashed refresh token for a user."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(refresh_token_hash=token_hash)
        )
        await self.session.flush()
    
    async def clear_refresh_token(self, user_id: UUID) -> None:
        """Clear refresh token for a user (logout)."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(refresh_token_hash=None)
        )
        await self.session.flush()
    
    async def verify_user(self, user_id: UUID) -> None:
        """Mark user as verified."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True)
        )
        await self.session.flush()
    
    async def deactivate_user(self, user_id: UUID) -> None:
        """Deactivate a user."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        await self.session.flush()
    
    async def company_code_exists(self, company_code: str) -> bool:
        """Check if a company code already exists."""
        result = await self.session.execute(
            select(func.count()).where(User.company_code == company_code)
        )
        return result.scalar_one() > 0
    
    async def list_all_users(
        self,
        company_id: Optional[UUID] = None,
        role: Optional[UserRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[User], int]:
        """List all users with optional filters."""
        # Count query
        count_query = select(func.count()).select_from(User)
        if company_id:
            count_query = count_query.where(User.company_id == str(company_id))
        if role:
            count_query = count_query.where(User.role == role)
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Data query
        query = select(User).order_by(User.created_at.desc())
        if company_id:
            query = query.where(User.company_id == str(company_id))
        if role:
            query = query.where(User.role == role)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        users = list(result.scalars().all())
        
        return users, total
    
    async def count_all(self) -> int:
        """Count all users."""
        result = await self.session.execute(
            select(func.count()).select_from(User)
        )
        return result.scalar() or 0


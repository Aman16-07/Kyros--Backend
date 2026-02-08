"""FastAPI dependencies."""

from typing import Annotated, AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import verify_access_token
from app.models.user import User, UserRole


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Type alias for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db_session)]

# Security scheme
security = HTTPBearer(auto_error=False)
security_required = HTTPBearer(auto_error=True)


async def get_current_user_optional(
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.
    Use this for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None
    
    user_id = verify_access_token(credentials.credentials)
    if user_id is None:
        return None
    
    from app.repositories.user_repo import UserRepository
    
    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))
    
    if user is None or not user.is_active:
        return None
    
    return user


async def get_current_user(
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_required)],
) -> User:
    """
    Get the current authenticated user.
    Raises 401 if not authenticated or token is invalid.
    """
    user_id = verify_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from app.repositories.user_repo import UserRepository
    
    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    return user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current user if they are an admin or super admin.
    Raises 403 if user is not an admin.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_super_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current user if they are a super admin (Kyros system admin).
    Raises 403 if user is not a super admin.
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user


async def get_current_manager_or_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current user if they are a manager or admin.
    Raises 403 if user doesn't have sufficient privileges.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required",
        )
    return current_user


# Type aliases for common dependency patterns
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]
SuperAdminUser = Annotated[User, Depends(require_super_admin)]
ManagerOrAdmin = Annotated[User, Depends(get_current_manager_or_admin)]


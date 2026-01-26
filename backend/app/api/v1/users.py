"""Users API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession
from app.models.user import UserRole
from app.repositories.user_repo import UserRepository
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
    data: UserCreate,
    db: DBSession,
) -> UserResponse:
    """Create a new user."""
    repo = UserRepository(db)
    
    # Check if user with same name exists
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this name already exists",
        )
    
    user = await repo.create(name=data.name, role=data.role)
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=UserListResponse,
    summary="Get all users",
)
async def get_users(
    db: DBSession,
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> UserListResponse:
    """Get all users with optional filtering."""
    repo = UserRepository(db)
    
    if role:
        users = await repo.get_by_role(role, skip, limit)
        total = await repo.count(role=role)
    else:
        users = await repo.get_all(skip, limit)
        total = await repo.count()
    
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID",
)
async def get_user(
    user_id: UUID,
    db: DBSession,
) -> UserResponse:
    """Get a user by ID."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: DBSession,
) -> UserResponse:
    """Update a user."""
    repo = UserRepository(db)
    
    update_data = data.model_dump(exclude_unset=True)
    user = await repo.update(user_id, **update_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(
    user_id: UUID,
    db: DBSession,
) -> None:
    """Delete a user."""
    repo = UserRepository(db)
    deleted = await repo.delete(user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

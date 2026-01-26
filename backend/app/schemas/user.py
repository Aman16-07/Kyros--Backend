"""User schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.models.user import UserRole
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class UserBase(BaseSchema):
    """Base user schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = Field(default=UserRole.VIEWER)


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    pass


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None


class UserResponse(UserBase, UUIDSchema, TimestampSchema):
    """Schema for user response."""
    
    pass


class UserListResponse(BaseSchema):
    """Schema for list of users."""
    
    items: list[UserResponse]
    total: int

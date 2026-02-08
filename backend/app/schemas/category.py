"""Category schemas."""

from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class CategoryBase(BaseSchema):
    """Base category schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    parent_id: Optional[UUID] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    
    pass


class CategoryUpdate(BaseSchema):
    """Schema for updating a category."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    parent_id: Optional[UUID] = None


class CategoryResponse(CategoryBase, UUIDSchema, TimestampSchema):
    """Schema for category response."""
    
    level: int = 0
    path: Optional[str] = None


class CategoryTree(CategoryResponse):
    """Schema for category with children (tree structure)."""
    
    children: list["CategoryTree"] = []


class CategoryListResponse(BaseSchema):
    """Schema for list of categories."""
    
    items: list[CategoryResponse]
    total: int


# Rebuild for forward reference
CategoryTree.model_rebuild()

"""Categories API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession
from app.repositories.category_repo import CategoryRepository
from app.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryTree,
    CategoryUpdate,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
)
async def create_category(
    data: CategoryCreate,
    db: DBSession,
) -> CategoryResponse:
    """Create a new category."""
    repo = CategoryRepository(db)
    
    # Verify parent exists if provided
    if data.parent_id:
        parent = await repo.get_by_id(data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )
    
    category = await repo.create(name=data.name, parent_id=data.parent_id)
    return CategoryResponse.model_validate(category)


@router.get(
    "",
    response_model=CategoryListResponse,
    summary="Get all categories",
)
async def get_categories(
    db: DBSession,
    parent_id: Optional[UUID] = Query(None, description="Filter by parent ID"),
    root_only: bool = Query(False, description="Get only root categories"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> CategoryListResponse:
    """Get all categories with optional filtering."""
    repo = CategoryRepository(db)
    
    if root_only:
        categories = await repo.get_root_categories(skip, limit)
        total = await repo.count(parent_id=None)
    elif parent_id:
        categories = await repo.get_children(parent_id, skip, limit)
        total = await repo.count(parent_id=parent_id)
    else:
        categories = await repo.get_all(skip, limit)
        total = await repo.count()
    
    return CategoryListResponse(
        items=[CategoryResponse.model_validate(c) for c in categories],
        total=total,
    )


@router.get(
    "/tree",
    response_model=list[CategoryTree],
    summary="Get category tree",
)
async def get_category_tree(
    db: DBSession,
) -> list[CategoryTree]:
    """Get full category tree structure."""
    repo = CategoryRepository(db)
    categories = await repo.get_tree()
    return [CategoryTree.model_validate(c) for c in categories]


@router.get(
    "/lookup",
    response_model=dict,
    summary="Lookup categories by name",
    description="Get a mapping of category names to their UUIDs. Useful for CSV uploads.",
)
async def lookup_categories_by_name(
    db: DBSession,
    names: list[str] = Query(..., description="List of category names to lookup"),
) -> dict:
    """Lookup category IDs by name."""
    repo = CategoryRepository(db)
    result = {}
    for name in names:
        category = await repo.get_by_name(name)
        if category:
            result[name] = str(category.id)
        else:
            result[name] = None
    return result


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a category by ID",
)
async def get_category(
    category_id: UUID,
    db: DBSession,
) -> CategoryResponse:
    """Get a category by ID."""
    repo = CategoryRepository(db)
    category = await repo.get_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    return CategoryResponse.model_validate(category)


@router.get(
    "/{category_id}/children",
    response_model=CategoryListResponse,
    summary="Get category children",
)
async def get_category_children(
    category_id: UUID,
    db: DBSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> CategoryListResponse:
    """Get children of a category."""
    repo = CategoryRepository(db)
    
    # Verify category exists
    category = await repo.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    children = await repo.get_children(category_id, skip, limit)
    total = await repo.count(parent_id=category_id)
    
    return CategoryListResponse(
        items=[CategoryResponse.model_validate(c) for c in children],
        total=total,
    )


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category",
)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: DBSession,
) -> CategoryResponse:
    """Update a category."""
    repo = CategoryRepository(db)
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Verify new parent exists if updating parent_id
    if "parent_id" in update_data and update_data["parent_id"]:
        parent = await repo.get_by_id(update_data["parent_id"])
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )
        # Prevent circular reference
        if update_data["parent_id"] == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent",
            )
    
    category = await repo.update(category_id, **update_data)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    return CategoryResponse.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
)
async def delete_category(
    category_id: UUID,
    db: DBSession,
) -> None:
    """Delete a category and its children."""
    repo = CategoryRepository(db)
    deleted = await repo.delete(category_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

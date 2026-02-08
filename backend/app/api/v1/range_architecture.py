"""Phase 2 Range Architecture API endpoints.

Provides:
- GET    /range/{season_id}/architecture                → Get range architecture
- POST   /range/{season_id}/architecture                → Create range entry
- POST   /range/{season_id}/architecture/bulk           → Bulk create
- GET    /range/{season_id}/architecture/{id}            → Get single entry
- PATCH  /range/{season_id}/architecture/{id}            → Update entry
- DELETE /range/{season_id}/architecture/{id}            → Delete entry
- POST   /range/{season_id}/submit                      → Submit for approval
- POST   /range/{season_id}/approve                     → Approve range
- POST   /range/{season_id}/reject                      → Reject range
- GET    /range/{season_id}/compare/{prior_season_id}   → Compare ranges
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import CurrentUser, DBSession, ManagerOrAdmin
from app.models.user import User
from app.schemas.range_architecture import (
    RangeApproveRequest,
    RangeArchitectureBulkCreate,
    RangeArchitectureCreate,
    RangeArchitectureListResponse,
    RangeArchitectureResponse,
    RangeArchitectureUpdate,
    RangeComparisonResponse,
    RangeRejectRequest,
    RangeSubmitRequest,
)
from app.services.range_architecture_service import RangeArchitectureService

router = APIRouter(prefix="/range", tags=["Range Architecture (Phase 2)"])


# ─── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("/{season_id}/architecture", response_model=RangeArchitectureListResponse)
async def get_range_architecture(
    season_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> RangeArchitectureListResponse:
    """Get range architecture for a season."""
    service = RangeArchitectureService(db)
    items, total = await service.list_by_season(season_id, skip, limit)
    return RangeArchitectureListResponse(
        items=[RangeArchitectureResponse.model_validate(r) for r in items],
        total=total,
    )


@router.post(
    "/{season_id}/architecture",
    response_model=RangeArchitectureResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_range_architecture(
    season_id: UUID,
    data: RangeArchitectureCreate,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> RangeArchitectureResponse:
    """Create a new range architecture entry."""
    data.season_id = season_id
    service = RangeArchitectureService(db)
    arch = await service.create(data, user_id=current_user.id)
    return RangeArchitectureResponse.model_validate(arch)


@router.post(
    "/{season_id}/architecture/bulk",
    response_model=RangeArchitectureListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create_range_architecture(
    season_id: UUID,
    data: RangeArchitectureBulkCreate,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> RangeArchitectureListResponse:
    """Bulk create range architecture entries."""
    for item in data.items:
        item.season_id = season_id
    service = RangeArchitectureService(db)
    items = await service.bulk_create(data, user_id=current_user.id)
    return RangeArchitectureListResponse(
        items=[RangeArchitectureResponse.model_validate(r) for r in items],
        total=len(items),
    )


@router.get(
    "/{season_id}/architecture/{arch_id}",
    response_model=RangeArchitectureResponse,
)
async def get_range_architecture_by_id(
    season_id: UUID,
    arch_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> RangeArchitectureResponse:
    """Get a single range architecture entry."""
    service = RangeArchitectureService(db)
    arch = await service.get(arch_id)
    return RangeArchitectureResponse.model_validate(arch)


@router.patch(
    "/{season_id}/architecture/{arch_id}",
    response_model=RangeArchitectureResponse,
)
async def update_range_architecture(
    season_id: UUID,
    arch_id: UUID,
    data: RangeArchitectureUpdate,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> RangeArchitectureResponse:
    """Update a range architecture entry. Approved/locked ranges cannot be modified."""
    service = RangeArchitectureService(db)
    arch = await service.update(arch_id, data, user_id=current_user.id)
    return RangeArchitectureResponse.model_validate(arch)


@router.delete(
    "/{season_id}/architecture/{arch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_range_architecture(
    season_id: UUID,
    arch_id: UUID,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> None:
    """Delete a range architecture entry (draft only)."""
    service = RangeArchitectureService(db)
    await service.delete(arch_id, user_id=current_user.id)


# ─── Approval Workflow ────────────────────────────────────────────────────────

@router.post(
    "/{season_id}/submit",
    response_model=RangeArchitectureListResponse,
)
async def submit_for_approval(
    season_id: UUID,
    data: RangeSubmitRequest,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> RangeArchitectureListResponse:
    """Submit range architectures for approval review."""
    service = RangeArchitectureService(db)
    items = await service.submit_for_approval(season_id, data, user_id=current_user.id)
    return RangeArchitectureListResponse(
        items=[RangeArchitectureResponse.model_validate(r) for r in items],
        total=len(items),
    )


@router.post(
    "/{season_id}/approve",
    response_model=RangeArchitectureListResponse,
)
async def approve_range(
    season_id: UUID,
    data: RangeApproveRequest,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> RangeArchitectureListResponse:
    """Approve range architectures."""
    service = RangeArchitectureService(db)
    items = await service.approve(season_id, data, user_id=current_user.id)
    return RangeArchitectureListResponse(
        items=[RangeArchitectureResponse.model_validate(r) for r in items],
        total=len(items),
    )


@router.post(
    "/{season_id}/reject",
    response_model=RangeArchitectureListResponse,
)
async def reject_range(
    season_id: UUID,
    data: RangeRejectRequest,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> RangeArchitectureListResponse:
    """Reject range architectures back to draft with a comment."""
    service = RangeArchitectureService(db)
    items = await service.reject(season_id, data, user_id=current_user.id)
    return RangeArchitectureListResponse(
        items=[RangeArchitectureResponse.model_validate(r) for r in items],
        total=len(items),
    )


# ─── Comparison ───────────────────────────────────────────────────────────────

@router.get(
    "/{season_id}/compare/{prior_season_id}",
    response_model=RangeComparisonResponse,
)
async def compare_ranges(
    season_id: UUID,
    prior_season_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> RangeComparisonResponse:
    """Compare range architecture between current and prior season."""
    service = RangeArchitectureService(db)
    return await service.compare_seasons(season_id, prior_season_id)

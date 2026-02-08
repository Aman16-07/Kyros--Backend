"""Range Architecture service - business logic for range planning.

Implements:
- Range architecture CRUD with validation
- Approval workflow (Draft → Submitted → Under Review → Approved → Locked)
- Season-to-season comparison
- Business rules enforcement (RNG-001 through RNG-005)
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.range_architecture import RangeArchitecture, RangeStatus
from app.models.season import Season, SeasonStatus
from app.models.audit_log import AuditAction
from app.repositories.range_architecture_repo import RangeArchitectureRepository
from app.repositories.season_repo import SeasonRepository
from app.schemas.range_architecture import (
    RangeApproveRequest,
    RangeArchitectureCreate,
    RangeArchitectureBulkCreate,
    RangeArchitectureUpdate,
    RangeComparisonItem,
    RangeComparisonResponse,
    RangeRejectRequest,
    RangeSubmitRequest,
)
from app.services.audit_service import AuditService


class RangeArchitectureService:
    """Service for range architecture planning and approval workflow."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RangeArchitectureRepository(session)
        self.season_repo = SeasonRepository(session)
        self.audit = AuditService(session)

    # ─── CRUD ─────────────────────────────────────────────────────────────

    async def create(
        self, data: RangeArchitectureCreate, user_id: UUID,
    ) -> RangeArchitecture:
        """Create a single range architecture entry."""
        await self._validate_season(data.season_id)

        arch = await self.repo.create(
            season_id=data.season_id,
            category_id=data.category_id,
            price_band=data.price_band,
            fabric=data.fabric,
            color_family=data.color_family,
            style_type=data.style_type,
            planned_styles=data.planned_styles,
            planned_options=data.planned_options,
            planned_depth=data.planned_depth,
            status=RangeStatus.DRAFT,
            created_by=user_id,
        )

        await self.audit.log_create(
            entity_type="RangeArchitecture",
            entity_id=arch.id,
            user_id=user_id,
            season_id=data.season_id,
        )

        return arch

    async def bulk_create(
        self, data: RangeArchitectureBulkCreate, user_id: UUID,
    ) -> list[RangeArchitecture]:
        """Bulk create range architecture entries."""
        if not data.items:
            return []

        season_id = data.items[0].season_id
        await self._validate_season(season_id)

        created = []
        for item in data.items:
            arch = await self.repo.create(
                season_id=item.season_id,
                category_id=item.category_id,
                price_band=item.price_band,
                fabric=item.fabric,
                color_family=item.color_family,
                style_type=item.style_type,
                planned_styles=item.planned_styles,
                planned_options=item.planned_options,
                planned_depth=item.planned_depth,
                status=RangeStatus.DRAFT,
                created_by=user_id,
            )
            created.append(arch)

        await self.audit.log_create(
            entity_type="RangeArchitecture",
            entity_id=season_id,
            user_id=user_id,
            description=f"Bulk created {len(created)} range architecture entries",
            season_id=season_id,
        )

        return created

    async def get(self, arch_id: UUID) -> RangeArchitecture:
        """Get a single range architecture by ID."""
        arch = await self.repo.get_with_details(arch_id)
        if not arch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Range architecture not found",
            )
        return arch

    async def list_by_season(
        self, season_id: UUID, skip: int = 0, limit: int = 100,
    ) -> tuple[list[RangeArchitecture], int]:
        """List range architectures for a season."""
        items = await self.repo.get_by_season(season_id, skip, limit)
        total = await self.repo.count_by_season(season_id)
        return items, total

    async def update(
        self, arch_id: UUID, data: RangeArchitectureUpdate, user_id: UUID,
    ) -> RangeArchitecture:
        """Update a range architecture entry. RNG-004: Approved range is immutable."""
        arch = await self.repo.get_by_id(arch_id)
        if not arch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Range architecture not found",
            )

        # RNG-004 / RNG-005: Cannot edit approved/locked ranges
        if arch.status in (RangeStatus.APPROVED, RangeStatus.LOCKED):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Approved or locked range architecture cannot be modified",
            )

        update_data = data.model_dump(exclude_unset=True)
        updated = await self.repo.update(arch_id, **update_data)

        # RNG-005: If edited after submission, revert to draft
        if arch.status in (RangeStatus.SUBMITTED, RangeStatus.UNDER_REVIEW):
            updated.status = RangeStatus.DRAFT
            updated.submitted_by = None
            updated.submitted_at = None
            await self.session.flush()
            await self.session.refresh(updated)

        await self.audit.log_update(
            entity_type="RangeArchitecture",
            entity_id=arch_id,
            user_id=user_id,
            new_data=update_data,
            season_id=arch.season_id,
        )

        return updated

    async def delete(self, arch_id: UUID, user_id: UUID) -> bool:
        """Delete a range architecture entry (only drafts)."""
        arch = await self.repo.get_by_id(arch_id)
        if not arch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Range architecture not found",
            )
        if arch.status != RangeStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only draft range architectures can be deleted",
            )

        await self.repo.delete(arch_id)
        await self.audit.log_delete(
            entity_type="RangeArchitecture",
            entity_id=arch_id,
            user_id=user_id,
            season_id=arch.season_id,
        )
        return True

    # ─── Approval Workflow ────────────────────────────────────────────────

    async def submit_for_approval(
        self, season_id: UUID, data: RangeSubmitRequest, user_id: UUID,
    ) -> list[RangeArchitecture]:
        """Submit range architectures for review."""
        await self._validate_season(season_id)

        submitted = []
        for range_id in data.range_ids:
            arch = await self.repo.get_by_id(range_id)
            if not arch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Range architecture {range_id} not found",
                )
            if arch.season_id != season_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Range {range_id} does not belong to season {season_id}",
                )
            if arch.status not in (RangeStatus.DRAFT, RangeStatus.REJECTED):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Range {range_id} status is {arch.status.value}, can only submit draft or rejected",
                )

            arch.status = RangeStatus.SUBMITTED
            arch.submitted_by = user_id
            arch.submitted_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(arch)
            submitted.append(arch)

        await self.audit.log(
            entity_type="RangeArchitecture",
            entity_id=season_id,
            action=AuditAction.UPDATE,
            user_id=user_id,
            description=f"Submitted {len(submitted)} range architectures for approval",
            season_id=season_id,
        )

        return submitted

    async def approve(
        self, season_id: UUID, data: RangeApproveRequest, user_id: UUID,
    ) -> list[RangeArchitecture]:
        """Approve range architectures."""
        await self._validate_season(season_id)

        approved = []
        for range_id in data.range_ids:
            arch = await self.repo.get_by_id(range_id)
            if not arch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Range architecture {range_id} not found",
                )
            if arch.status not in (RangeStatus.SUBMITTED, RangeStatus.UNDER_REVIEW):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Range {range_id} status is {arch.status.value}, cannot approve",
                )

            arch.status = RangeStatus.APPROVED
            arch.reviewed_by = user_id
            arch.reviewed_at = datetime.now(timezone.utc)
            arch.review_comment = data.comment
            await self.session.flush()
            await self.session.refresh(arch)
            approved.append(arch)

        await self.audit.log(
            entity_type="RangeArchitecture",
            entity_id=season_id,
            action=AuditAction.APPROVE,
            user_id=user_id,
            description=f"Approved {len(approved)} range architectures",
            season_id=season_id,
        )

        return approved

    async def reject(
        self, season_id: UUID, data: RangeRejectRequest, user_id: UUID,
    ) -> list[RangeArchitecture]:
        """Reject range architectures back to draft."""
        await self._validate_season(season_id)

        rejected = []
        for range_id in data.range_ids:
            arch = await self.repo.get_by_id(range_id)
            if not arch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Range architecture {range_id} not found",
                )
            if arch.status not in (RangeStatus.SUBMITTED, RangeStatus.UNDER_REVIEW):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Range {range_id} status is {arch.status.value}, cannot reject",
                )

            arch.status = RangeStatus.REJECTED
            arch.reviewed_by = user_id
            arch.reviewed_at = datetime.now(timezone.utc)
            arch.review_comment = data.comment
            await self.session.flush()
            await self.session.refresh(arch)
            rejected.append(arch)

        await self.audit.log(
            entity_type="RangeArchitecture",
            entity_id=season_id,
            action=AuditAction.UPDATE,
            user_id=user_id,
            description=f"Rejected {len(rejected)} range architectures: {data.comment}",
            season_id=season_id,
        )

        return rejected

    # ─── Comparison ───────────────────────────────────────────────────────

    async def compare_seasons(
        self, current_season_id: UUID, prior_season_id: UUID,
    ) -> RangeComparisonResponse:
        """Compare range architecture between two seasons."""
        current_ranges = await self.repo.get_for_comparison(current_season_id)
        prior_ranges = await self.repo.get_for_comparison(prior_season_id)

        # Build lookup: (category_id, price_band, style_type) → range
        def _key(r: RangeArchitecture):
            return (r.category_id, r.price_band, r.style_type)

        prior_map = {}
        for r in prior_ranges:
            prior_map[_key(r)] = r

        items = []
        total_current_styles = 0
        total_prior_styles = 0

        for cr in current_ranges:
            key = _key(cr)
            pr = prior_map.pop(key, None)

            cs = cr.planned_styles or 0
            co = cr.planned_options or 0
            cd = cr.planned_depth or 0
            ps = pr.planned_styles or 0 if pr else 0
            po_val = pr.planned_options or 0 if pr else 0
            pd = pr.planned_depth or 0 if pr else 0

            total_current_styles += cs
            total_prior_styles += ps

            cat_name = cr.category.name if cr.category else None

            items.append(RangeComparisonItem(
                category_id=cr.category_id,
                category_name=cat_name,
                price_band=cr.price_band,
                style_type=cr.style_type,
                current_styles=cs,
                current_options=co,
                current_depth=cd,
                prior_styles=ps,
                prior_options=po_val,
                prior_depth=pd,
                styles_variance=cs - ps,
                options_variance=co - po_val,
                depth_variance=cd - pd,
            ))

        # Add prior-only entries
        for key, pr in prior_map.items():
            ps = pr.planned_styles or 0
            po_val = pr.planned_options or 0
            pd = pr.planned_depth or 0
            total_prior_styles += ps

            cat_name = pr.category.name if pr.category else None

            items.append(RangeComparisonItem(
                category_id=pr.category_id,
                category_name=cat_name,
                price_band=pr.price_band,
                style_type=pr.style_type,
                current_styles=0,
                current_options=0,
                current_depth=0,
                prior_styles=ps,
                prior_options=po_val,
                prior_depth=pd,
                styles_variance=-ps,
                options_variance=-po_val,
                depth_variance=-pd,
            ))

        return RangeComparisonResponse(
            current_season_id=current_season_id,
            prior_season_id=prior_season_id,
            items=items,
            total_current_styles=total_current_styles,
            total_prior_styles=total_prior_styles,
            total_styles_variance=total_current_styles - total_prior_styles,
        )

    # ─── Internal Helpers ─────────────────────────────────────────────────

    async def _validate_season(self, season_id: UUID) -> Season:
        season = await self.season_repo.get_by_id(season_id)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Season {season_id} not found",
            )
        if season.status == SeasonStatus.LOCKED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Season is locked and cannot be modified",
            )
        return season

"""Range Architecture schemas for Phase 2 range planning."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.range_architecture import RangeStatus
from app.schemas.base import BaseSchema, UUIDSchema


# ─── Range Architecture Schemas ──────────────────────────────────────────────

class RangeArchitectureBase(BaseSchema):
    season_id: UUID
    category_id: Optional[UUID] = None
    price_band: Optional[str] = Field(None, max_length=50)
    fabric: Optional[str] = Field(None, max_length=100)
    color_family: Optional[str] = Field(None, max_length=100)
    style_type: Optional[str] = Field(None, max_length=20)
    planned_styles: Optional[int] = Field(None, ge=0)
    planned_options: Optional[int] = Field(None, ge=0)
    planned_depth: Optional[int] = Field(None, ge=0)


class RangeArchitectureCreate(RangeArchitectureBase):
    pass


class RangeArchitectureBulkCreate(BaseSchema):
    items: list[RangeArchitectureCreate]


class RangeArchitectureUpdate(BaseSchema):
    category_id: Optional[UUID] = None
    price_band: Optional[str] = Field(None, max_length=50)
    fabric: Optional[str] = Field(None, max_length=100)
    color_family: Optional[str] = Field(None, max_length=100)
    style_type: Optional[str] = Field(None, max_length=20)
    planned_styles: Optional[int] = Field(None, ge=0)
    planned_options: Optional[int] = Field(None, ge=0)
    planned_depth: Optional[int] = Field(None, ge=0)


class RangeArchitectureResponse(RangeArchitectureBase, UUIDSchema):
    status: RangeStatus
    submitted_by: Optional[UUID] = None
    submitted_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_comment: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class RangeArchitectureDetail(RangeArchitectureResponse):
    """With enriched names for display."""
    season_name: Optional[str] = None
    category_name: Optional[str] = None
    submitter_name: Optional[str] = None
    reviewer_name: Optional[str] = None


class RangeArchitectureListResponse(BaseSchema):
    items: list[RangeArchitectureResponse]
    total: int


# ─── Range Approval Schemas ──────────────────────────────────────────────────

class RangeSubmitRequest(BaseSchema):
    """Submit range architecture for approval."""
    range_ids: list[UUID] = Field(..., min_length=1)


class RangeApproveRequest(BaseSchema):
    """Approve or reject range architecture."""
    range_ids: list[UUID] = Field(..., min_length=1)
    comment: Optional[str] = Field(None, max_length=1000)


class RangeRejectRequest(BaseSchema):
    """Reject range architecture."""
    range_ids: list[UUID] = Field(..., min_length=1)
    comment: str = Field(..., min_length=10, max_length=1000)


# ─── Range Comparison Schemas ────────────────────────────────────────────────

class RangeComparisonItem(BaseSchema):
    """Single row in range comparison."""
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    price_band: Optional[str] = None
    style_type: Optional[str] = None
    current_styles: Optional[int] = None
    current_options: Optional[int] = None
    current_depth: Optional[int] = None
    prior_styles: Optional[int] = None
    prior_options: Optional[int] = None
    prior_depth: Optional[int] = None
    styles_variance: Optional[int] = None
    options_variance: Optional[int] = None
    depth_variance: Optional[int] = None


class RangeComparisonResponse(BaseSchema):
    """Full range comparison between two seasons."""
    current_season_id: UUID
    prior_season_id: UUID
    items: list[RangeComparisonItem]
    total_current_styles: int = 0
    total_prior_styles: int = 0
    total_styles_variance: int = 0

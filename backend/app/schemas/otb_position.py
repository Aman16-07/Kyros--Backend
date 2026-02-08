"""OTB Position and Adjustment schemas for Phase 2 dynamic OTB management."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.otb_adjustment import AdjustmentStatus
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


# ─── OTB Position Schemas ────────────────────────────────────────────────────

class OTBPositionBase(BaseSchema):
    season_id: UUID
    category_id: Optional[UUID] = None
    month: date
    planned_otb: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    consumed_otb: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    available_otb: Decimal = Field(default=Decimal("0.00"), decimal_places=2)

    @field_validator("month")
    @classmethod
    def normalize_month(cls, v: date) -> date:
        return v.replace(day=1)


class OTBPositionCreate(OTBPositionBase):
    pass


class OTBPositionUpdate(BaseSchema):
    planned_otb: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    consumed_otb: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    available_otb: Optional[Decimal] = Field(None, decimal_places=2)


class OTBPositionResponse(OTBPositionBase, UUIDSchema):
    last_calculated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    consumption_percentage: Optional[Decimal] = None
    is_low: Optional[bool] = None
    is_exceeded: Optional[bool] = None


class OTBPositionDetail(OTBPositionResponse):
    """Position with enriched category/season info."""
    season_name: Optional[str] = None
    category_name: Optional[str] = None


class OTBPositionListResponse(BaseSchema):
    items: list[OTBPositionResponse]
    total: int


# ─── OTB Dashboard Schemas ───────────────────────────────────────────────────

class OTBCategorySummary(BaseSchema):
    """Per-category OTB summary for dashboard."""
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    total_planned: Decimal = Decimal("0.00")
    total_consumed: Decimal = Decimal("0.00")
    total_available: Decimal = Decimal("0.00")
    consumption_percentage: Decimal = Decimal("0.00")


class OTBMonthSummary(BaseSchema):
    """Per-month OTB position for dashboard."""
    month: date
    planned_otb: Decimal = Decimal("0.00")
    consumed_otb: Decimal = Decimal("0.00")
    available_otb: Decimal = Decimal("0.00")
    consumption_percentage: Decimal = Decimal("0.00")


class OTBDashboardResponse(BaseSchema):
    """Full OTB dashboard response."""
    season_id: UUID
    total_planned: Decimal = Decimal("0.00")
    total_consumed: Decimal = Decimal("0.00")
    total_available: Decimal = Decimal("0.00")
    consumption_percentage: Decimal = Decimal("0.00")
    by_category: list[OTBCategorySummary] = []
    by_month: list[OTBMonthSummary] = []


class OTBConsumptionResponse(BaseSchema):
    """OTB consumption tracking details."""
    season_id: UUID
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    total_po_value: Decimal = Decimal("0.00")
    consumed_otb: Decimal = Decimal("0.00")
    available_otb: Decimal = Decimal("0.00")
    consumption_percentage: Decimal = Decimal("0.00")
    projected_exhaustion_date: Optional[date] = None


class OTBConsumptionListResponse(BaseSchema):
    items: list[OTBConsumptionResponse]


class OTBForecastResponse(BaseSchema):
    """Projected OTB outlook."""
    season_id: UUID
    month: date
    projected_consumption: Decimal = Decimal("0.00")
    projected_remaining: Decimal = Decimal("0.00")
    trend: str = "stable"  # "increasing", "decreasing", "stable"


class OTBForecastListResponse(BaseSchema):
    items: list[OTBForecastResponse]


# ─── OTB Adjustment Schemas ──────────────────────────────────────────────────

class OTBAdjustmentBase(BaseSchema):
    season_id: UUID
    from_category_id: Optional[UUID] = None
    to_category_id: Optional[UUID] = None
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    reason: str = Field(..., min_length=10, max_length=2000)


class OTBAdjustmentCreate(OTBAdjustmentBase):
    pass


class OTBAdjustmentApprove(BaseSchema):
    pass


class OTBAdjustmentReject(BaseSchema):
    rejection_reason: str = Field(..., min_length=10, max_length=1000)


class OTBAdjustmentResponse(OTBAdjustmentBase, UUIDSchema):
    status: AdjustmentStatus
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime


class OTBAdjustmentDetail(OTBAdjustmentResponse):
    from_category_name: Optional[str] = None
    to_category_name: Optional[str] = None
    approver_name: Optional[str] = None
    creator_name: Optional[str] = None


class OTBAdjustmentListResponse(BaseSchema):
    items: list[OTBAdjustmentResponse]
    total: int


# ─── OTB Alert Schemas ───────────────────────────────────────────────────────

class OTBAlert(BaseSchema):
    """OTB alert for threshold violations."""
    alert_type: str  # low_otb, otb_exceeded, underutilized, category_imbalance
    severity: str  # warning, critical
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    message: str
    current_value: Decimal
    threshold_value: Decimal
    season_id: UUID


class OTBAlertListResponse(BaseSchema):
    items: list[OTBAlert]

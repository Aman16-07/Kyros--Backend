"""Phase 2 OTB Management API endpoints.

Provides:
- GET  /otb-management/{season_id}/position       → Current OTB position
- GET  /otb-management/{season_id}/dashboard       → Full OTB dashboard
- GET  /otb-management/{season_id}/consumption     → Consumption details
- GET  /otb-management/{season_id}/forecast        → Projected OTB
- GET  /otb-management/{season_id}/alerts          → OTB alerts
- POST /otb-management/{season_id}/recalculate     → Force recalculation
- POST /otb-management/{season_id}/adjust          → Create adjustment
- GET  /otb-management/{season_id}/adjustments     → List adjustments
- POST /otb-management/adjustments/{id}/approve    → Approve adjustment
- POST /otb-management/adjustments/{id}/reject     → Reject adjustment
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import CurrentUser, DBSession, ManagerOrAdmin
from app.models.user import User
from app.schemas.otb_position import (
    OTBAdjustmentCreate,
    OTBAdjustmentListResponse,
    OTBAdjustmentReject,
    OTBAdjustmentResponse,
    OTBAlertListResponse,
    OTBConsumptionListResponse,
    OTBDashboardResponse,
    OTBForecastListResponse,
    OTBPositionListResponse,
    OTBPositionResponse,
)
from app.services.otb_calculation_engine import OTBCalculationEngine

router = APIRouter(prefix="/otb-management", tags=["OTB Management (Phase 2)"])


# ─── OTB Position & Dashboard ────────────────────────────────────────────────

@router.get("/{season_id}/position", response_model=OTBPositionListResponse)
async def get_otb_position(
    season_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> OTBPositionListResponse:
    """Get current OTB position for a season (recalculates automatically)."""
    engine = OTBCalculationEngine(db)
    positions = await engine.get_position(season_id)
    total = await engine.get_position_count(season_id)
    return OTBPositionListResponse(
        items=[OTBPositionResponse.model_validate(p) for p in positions],
        total=total,
    )


@router.get("/{season_id}/dashboard", response_model=OTBDashboardResponse)
async def get_otb_dashboard(
    season_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> OTBDashboardResponse:
    """Get full OTB dashboard with summary, category breakdown, and monthly view."""
    engine = OTBCalculationEngine(db)
    return await engine.get_dashboard(season_id)


@router.get("/{season_id}/consumption", response_model=OTBConsumptionListResponse)
async def get_otb_consumption(
    season_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> OTBConsumptionListResponse:
    """Get OTB consumption details per category with projected exhaustion."""
    engine = OTBCalculationEngine(db)
    return await engine.get_consumption(season_id)


@router.get("/{season_id}/forecast", response_model=OTBForecastListResponse)
async def get_otb_forecast(
    season_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> OTBForecastListResponse:
    """Get projected OTB for remaining months based on consumption trends."""
    engine = OTBCalculationEngine(db)
    return await engine.get_forecast(season_id)


@router.get("/{season_id}/alerts", response_model=OTBAlertListResponse)
async def get_otb_alerts(
    season_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> OTBAlertListResponse:
    """Get OTB alerts for threshold violations (low, exceeded, underutilized, imbalance)."""
    engine = OTBCalculationEngine(db)
    return await engine.get_alerts(season_id)


@router.post(
    "/{season_id}/recalculate",
    response_model=OTBPositionListResponse,
    status_code=status.HTTP_200_OK,
)
async def recalculate_otb(
    season_id: UUID,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> OTBPositionListResponse:
    """Force recalculation of all OTB positions for a season."""
    engine = OTBCalculationEngine(db)
    positions = await engine.recalculate_season(season_id)
    return OTBPositionListResponse(
        items=[OTBPositionResponse.model_validate(p) for p in positions],
        total=len(positions),
    )


# ─── OTB Adjustments ─────────────────────────────────────────────────────────

@router.post(
    "/{season_id}/adjust",
    response_model=OTBAdjustmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_adjustment(
    season_id: UUID,
    data: OTBAdjustmentCreate,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> OTBAdjustmentResponse:
    """Create an OTB adjustment to rebalance budget between categories."""
    data.season_id = season_id
    engine = OTBCalculationEngine(db)
    adj = await engine.create_adjustment(data, user_id=current_user.id)
    return OTBAdjustmentResponse.model_validate(adj)


@router.get("/{season_id}/adjustments", response_model=OTBAdjustmentListResponse)
async def list_adjustments(
    season_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> OTBAdjustmentListResponse:
    """List all OTB adjustments for a season."""
    engine = OTBCalculationEngine(db)
    items, total = await engine.get_adjustments(season_id, skip, limit)
    return OTBAdjustmentListResponse(
        items=[OTBAdjustmentResponse.model_validate(a) for a in items],
        total=total,
    )


@router.post(
    "/adjustments/{adjustment_id}/approve",
    response_model=OTBAdjustmentResponse,
)
async def approve_adjustment(
    adjustment_id: UUID,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> OTBAdjustmentResponse:
    """Approve a pending OTB adjustment and recalculate affected positions."""
    engine = OTBCalculationEngine(db)
    adj = await engine.approve_adjustment(adjustment_id, approver_id=current_user.id)
    return OTBAdjustmentResponse.model_validate(adj)


@router.post(
    "/adjustments/{adjustment_id}/reject",
    response_model=OTBAdjustmentResponse,
)
async def reject_adjustment(
    adjustment_id: UUID,
    data: OTBAdjustmentReject,
    db: DBSession,
    current_user: ManagerOrAdmin,
) -> OTBAdjustmentResponse:
    """Reject a pending OTB adjustment."""
    engine = OTBCalculationEngine(db)
    adj = await engine.reject_adjustment(adjustment_id, reviewer_id=current_user.id, data=data)
    return OTBAdjustmentResponse.model_validate(adj)

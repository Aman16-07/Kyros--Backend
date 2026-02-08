"""Phase 2 OTB Calculation Engine - dynamic OTB management.

Implements:
- Real-time OTB position calculation from OTB plans and POs
- Consumption tracking per category/month
- Dashboard aggregations
- Alerts for threshold violations
- OTB adjustments with approval workflow
- Forecasting projections
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.otb_adjustment import AdjustmentStatus, OTBAdjustment
from app.models.otb_plan import OTBPlan
from app.models.otb_position import OTBPosition
from app.models.purchase_order import POStatus, PurchaseOrder
from app.models.season import Season, SeasonStatus
from app.models.category import Category
from app.models.audit_log import AuditAction
from app.repositories.otb_position_repo import OTBPositionRepository
from app.repositories.otb_adjustment_repo import OTBAdjustmentRepository
from app.repositories.season_repo import SeasonRepository
from app.schemas.otb_position import (
    OTBAlert,
    OTBAlertListResponse,
    OTBCategorySummary,
    OTBConsumptionResponse,
    OTBConsumptionListResponse,
    OTBDashboardResponse,
    OTBForecastResponse,
    OTBForecastListResponse,
    OTBMonthSummary,
    OTBAdjustmentCreate,
    OTBAdjustmentReject,
    OTBPositionCreate,
    OTBPositionResponse,
)
from app.services.audit_service import AuditService


# Alert threshold defaults (configurable per-user in future)
DEFAULT_LOW_OTB_THRESHOLD = Decimal("20.00")  # 20%
DEFAULT_UNDERUTILIZED_THRESHOLD = Decimal("50.00")  # 50%
DEFAULT_IMBALANCE_THRESHOLD = Decimal("25.00")  # 25% variance


class OTBCalculationEngine:
    """Phase 2 dynamic OTB calculation engine.

    Core responsibilities:
    - Calculate and maintain OTB positions from plan data + PO consumption
    - Support real-time recalculation when POs change
    - Generate alerts on threshold violations
    - Handle OTB adjustments between categories
    - Provide dashboard/consumption/forecast data
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.position_repo = OTBPositionRepository(session)
        self.adjustment_repo = OTBAdjustmentRepository(session)
        self.season_repo = SeasonRepository(session)
        self.audit = AuditService(session)

    # ─── Core Calculation ─────────────────────────────────────────────────

    async def recalculate_season(self, season_id: UUID) -> list[OTBPosition]:
        """Recalculate all OTB positions for a season from plan data and POs.

        OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order
        consumed_otb = sum of active PO values for that category/month
        available_otb = planned_otb - consumed_otb
        """
        season = await self._get_season(season_id)

        # 1. Get all OTB plan rows grouped by category + month
        planned = await self._get_planned_otb_by_category_month(season_id)

        # 2. Get PO consumption grouped by category + month
        consumed = await self._get_consumed_otb_by_category_month(season_id)

        # 3. Get approved adjustments to factor in
        adjustments = await self._get_approved_adjustment_totals(season_id)

        # 4. Upsert OTB positions
        positions = []
        for key, planned_otb in planned.items():
            category_id, month = key
            # Apply adjustments
            adj_in = adjustments.get(("to", category_id), Decimal("0.00"))
            adj_out = adjustments.get(("from", category_id), Decimal("0.00"))

            effective_planned = planned_otb + adj_in - adj_out
            consumed_otb = consumed.get(key, Decimal("0.00"))
            available_otb = max(effective_planned - consumed_otb, Decimal("0.00"))

            position = await self.position_repo.upsert(
                season_id=season_id,
                category_id=category_id,
                month=month,
                planned_otb=effective_planned,
                consumed_otb=consumed_otb,
                available_otb=available_otb,
            )
            positions.append(position)

        return positions

    async def recalculate_category(
        self, season_id: UUID, category_id: UUID,
    ) -> list[OTBPosition]:
        """Recalculate OTB positions for a specific category in a season."""
        await self._get_season(season_id)

        planned = await self._get_planned_otb_by_category_month(
            season_id, category_id=category_id,
        )
        consumed = await self._get_consumed_otb_by_category_month(
            season_id, category_id=category_id,
        )
        adjustments = await self._get_approved_adjustment_totals(
            season_id, category_id=category_id,
        )

        positions = []
        for key, planned_otb in planned.items():
            cat_id, month = key
            adj_in = adjustments.get(("to", cat_id), Decimal("0.00"))
            adj_out = adjustments.get(("from", cat_id), Decimal("0.00"))

            effective_planned = planned_otb + adj_in - adj_out
            consumed_otb = consumed.get(key, Decimal("0.00"))
            available_otb = max(effective_planned - consumed_otb, Decimal("0.00"))

            position = await self.position_repo.upsert(
                season_id=season_id,
                category_id=cat_id,
                month=month,
                planned_otb=effective_planned,
                consumed_otb=consumed_otb,
                available_otb=available_otb,
            )
            positions.append(position)

        return positions

    # ─── Dashboard ────────────────────────────────────────────────────────

    async def get_dashboard(self, season_id: UUID) -> OTBDashboardResponse:
        """Get full OTB dashboard data for a season."""
        await self._get_season(season_id)

        # Ensure positions are up to date
        await self.recalculate_season(season_id)

        totals = await self.position_repo.get_season_totals(season_id)
        cat_summary = await self.position_repo.get_category_summary(season_id)
        month_summary = await self.position_repo.get_month_summary(season_id)

        total_planned = totals["total_planned"]
        total_consumed = totals["total_consumed"]
        total_available = totals["total_available"]
        consumption_pct = (
            round((total_consumed / total_planned) * 100, 2)
            if total_planned > 0
            else Decimal("0.00")
        )

        # Enrich category summaries with names
        by_category = []
        for cs in cat_summary:
            cat_name = None
            if cs["category_id"]:
                cat = await self.session.get(Category, cs["category_id"])
                cat_name = cat.name if cat else None
            tp = cs["total_planned"]
            tc = cs["total_consumed"]
            pct = round((tc / tp) * 100, 2) if tp > 0 else Decimal("0.00")
            by_category.append(OTBCategorySummary(
                category_id=cs["category_id"],
                category_name=cat_name,
                total_planned=tp,
                total_consumed=tc,
                total_available=cs["total_available"],
                consumption_percentage=pct,
            ))

        # Month summaries
        by_month = []
        for ms in month_summary:
            p = ms["planned_otb"]
            c = ms["consumed_otb"]
            pct = round((c / p) * 100, 2) if p > 0 else Decimal("0.00")
            by_month.append(OTBMonthSummary(
                month=ms["month"],
                planned_otb=p,
                consumed_otb=c,
                available_otb=ms["available_otb"],
                consumption_percentage=pct,
            ))

        return OTBDashboardResponse(
            season_id=season_id,
            total_planned=total_planned,
            total_consumed=total_consumed,
            total_available=total_available,
            consumption_percentage=consumption_pct,
            by_category=by_category,
            by_month=by_month,
        )

    # ─── Consumption Tracking ─────────────────────────────────────────────

    async def get_consumption(self, season_id: UUID) -> OTBConsumptionListResponse:
        """Get consumption details per category."""
        await self._get_season(season_id)
        await self.recalculate_season(season_id)

        cat_summary = await self.position_repo.get_category_summary(season_id)
        items = []
        for cs in cat_summary:
            cat_name = None
            if cs["category_id"]:
                cat = await self.session.get(Category, cs["category_id"])
                cat_name = cat.name if cat else None
            tp = cs["total_planned"]
            tc = cs["total_consumed"]
            ta = cs["total_available"]
            pct = round((tc / tp) * 100, 2) if tp > 0 else Decimal("0.00")

            # Simple projected exhaustion: if consumption rate > 0
            projected_date = None
            if tc > 0 and ta > 0:
                # Naive projection based on even consumption rate
                from datetime import timedelta
                days_elapsed = max((datetime.now(timezone.utc) - datetime(2026, 1, 1, tzinfo=timezone.utc)).days, 1)
                daily_rate = tc / days_elapsed
                if daily_rate > 0:
                    days_remaining = int(ta / daily_rate)
                    projected_date = (datetime.now(timezone.utc) + timedelta(days=days_remaining)).date()

            items.append(OTBConsumptionResponse(
                season_id=season_id,
                category_id=cs["category_id"],
                category_name=cat_name,
                total_po_value=tc,
                consumed_otb=tc,
                available_otb=ta,
                consumption_percentage=pct,
                projected_exhaustion_date=projected_date,
            ))

        return OTBConsumptionListResponse(items=items)

    # ─── Forecasting ──────────────────────────────────────────────────────

    async def get_forecast(self, season_id: UUID) -> OTBForecastListResponse:
        """Get projected OTB for remaining months."""
        await self._get_season(season_id)
        await self.recalculate_season(season_id)

        month_data = await self.position_repo.get_month_summary(season_id)
        today = date.today()

        items = []
        # Calculate average monthly consumption from past months
        past_months = [m for m in month_data if m["month"] < today.replace(day=1)]
        total_past_consumed = sum((m["consumed_otb"] for m in past_months), Decimal("0"))
        num_past_months = len(past_months) if past_months else 1
        avg_monthly_consumption = total_past_consumed / Decimal(num_past_months)

        running_remaining = sum((m["available_otb"] for m in month_data), Decimal("0"))

        for md in month_data:
            if md["month"] >= today.replace(day=1):
                projected_consumption = avg_monthly_consumption
                running_remaining -= projected_consumption
                trend = "stable"
                if avg_monthly_consumption > md["planned_otb"] * Decimal("0.8"):
                    trend = "increasing"
                elif avg_monthly_consumption < md["planned_otb"] * Decimal("0.3"):
                    trend = "decreasing"

                items.append(OTBForecastResponse(
                    season_id=season_id,
                    month=md["month"],
                    projected_consumption=round(projected_consumption, 2),
                    projected_remaining=round(max(running_remaining, Decimal("0.00")), 2),
                    trend=trend,
                ))

        return OTBForecastListResponse(items=items)

    # ─── Alerts ───────────────────────────────────────────────────────────

    async def get_alerts(self, season_id: UUID) -> OTBAlertListResponse:
        """Generate alerts for the season based on current OTB positions."""
        await self._get_season(season_id)
        await self.recalculate_season(season_id)

        cat_summary = await self.position_repo.get_category_summary(season_id)
        alerts = []

        # Compute average planned across categories for imbalance check
        all_planned = [cs["total_planned"] for cs in cat_summary if cs["total_planned"] > 0]
        avg_planned = sum(all_planned) / len(all_planned) if all_planned else Decimal("0.00")

        for cs in cat_summary:
            cat_name = None
            if cs["category_id"]:
                cat = await self.session.get(Category, cs["category_id"])
                cat_name = cat.name if cat else None

            tp = cs["total_planned"]
            tc = cs["total_consumed"]
            ta = cs["total_available"]

            if tp <= 0:
                continue

            pct = round((tc / tp) * 100, 2)

            # Low OTB: available < 20% of planned
            if ta < tp * (DEFAULT_LOW_OTB_THRESHOLD / 100):
                alerts.append(OTBAlert(
                    alert_type="low_otb",
                    severity="warning",
                    category_id=cs["category_id"],
                    category_name=cat_name,
                    message=f"OTB for {cat_name or 'Unknown'} is below {DEFAULT_LOW_OTB_THRESHOLD}% — only {ta:.2f} remaining",
                    current_value=ta,
                    threshold_value=round(tp * DEFAULT_LOW_OTB_THRESHOLD / 100, 2),
                    season_id=season_id,
                ))

            # OTB exceeded
            if tc > tp:
                alerts.append(OTBAlert(
                    alert_type="otb_exceeded",
                    severity="critical",
                    category_id=cs["category_id"],
                    category_name=cat_name,
                    message=f"OTB for {cat_name or 'Unknown'} exceeded! Consumed {tc:.2f} vs planned {tp:.2f}",
                    current_value=tc,
                    threshold_value=tp,
                    season_id=season_id,
                ))

            # Underutilized: consumed < 50% at mid-season
            if pct < DEFAULT_UNDERUTILIZED_THRESHOLD:
                alerts.append(OTBAlert(
                    alert_type="underutilized",
                    severity="warning",
                    category_id=cs["category_id"],
                    category_name=cat_name,
                    message=f"OTB for {cat_name or 'Unknown'} is underutilized — only {pct}% consumed",
                    current_value=pct,
                    threshold_value=DEFAULT_UNDERUTILIZED_THRESHOLD,
                    season_id=season_id,
                ))

            # Category imbalance: variance from average > 25%
            if avg_planned > 0:
                variance_pct = abs(tp - avg_planned) / avg_planned * 100
                if variance_pct > DEFAULT_IMBALANCE_THRESHOLD:
                    alerts.append(OTBAlert(
                        alert_type="category_imbalance",
                        severity="warning",
                        category_id=cs["category_id"],
                        category_name=cat_name,
                        message=f"Category {cat_name or 'Unknown'} has {variance_pct:.1f}% variance from average OTB",
                        current_value=tp,
                        threshold_value=avg_planned,
                        season_id=season_id,
                    ))

        return OTBAlertListResponse(items=alerts)

    # ─── OTB Position CRUD ────────────────────────────────────────────────

    async def get_position(self, season_id: UUID) -> list[OTBPosition]:
        """Get all OTB positions for a season."""
        await self._get_season(season_id)
        return await self.position_repo.get_by_season(season_id, limit=1000)

    async def get_position_count(self, season_id: UUID) -> int:
        return await self.position_repo.count(season_id=season_id)

    # ─── Adjustments ──────────────────────────────────────────────────────

    async def create_adjustment(
        self,
        data: OTBAdjustmentCreate,
        user_id: UUID,
    ) -> OTBAdjustment:
        """Create a new OTB adjustment request."""
        season = await self._get_season(data.season_id)

        # OTB-003: Locked seasons cannot have adjustments
        if season.status == SeasonStatus.LOCKED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create adjustments for locked seasons",
            )

        # OTB-001: Validate source category has enough available OTB
        if data.from_category_id:
            positions = await self.position_repo.get_by_season_and_category(
                data.season_id, data.from_category_id,
            )
            total_available = sum(p.available_otb for p in positions)
            if total_available < data.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient OTB in source category. Available: {total_available}, Requested: {data.amount}",
                )

        adjustment = await self.adjustment_repo.create(
            season_id=data.season_id,
            from_category_id=data.from_category_id,
            to_category_id=data.to_category_id,
            amount=data.amount,
            reason=data.reason,
            status=AdjustmentStatus.PENDING,
            created_by=user_id,
        )

        await self.audit.log_create(
            entity_type="OTBAdjustment",
            entity_id=adjustment.id,
            user_id=user_id,
            new_data={
                "from_category_id": str(data.from_category_id) if data.from_category_id else None,
                "to_category_id": str(data.to_category_id) if data.to_category_id else None,
                "amount": float(data.amount),
                "reason": data.reason,
            },
            season_id=data.season_id,
        )

        return adjustment

    async def approve_adjustment(
        self, adjustment_id: UUID, approver_id: UUID,
    ) -> OTBAdjustment:
        """Approve an OTB adjustment and recalculate positions."""
        adj = await self.adjustment_repo.get_by_id(adjustment_id)
        if not adj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adjustment not found",
            )
        if adj.status != AdjustmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Adjustment is already {adj.status.value}",
            )

        adj.status = AdjustmentStatus.APPROVED
        adj.approved_by = approver_id
        adj.approved_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(adj)

        # Recalculate affected categories
        if adj.from_category_id:
            await self.recalculate_category(adj.season_id, adj.from_category_id)
        if adj.to_category_id:
            await self.recalculate_category(adj.season_id, adj.to_category_id)

        await self.audit.log(
            entity_type="OTBAdjustment",
            entity_id=adjustment_id,
            action=AuditAction.APPROVE,
            user_id=approver_id,
            description=f"Approved adjustment of {adj.amount}",
            season_id=adj.season_id,
        )

        return adj

    async def reject_adjustment(
        self, adjustment_id: UUID, reviewer_id: UUID, data: OTBAdjustmentReject,
    ) -> OTBAdjustment:
        """Reject an OTB adjustment."""
        adj = await self.adjustment_repo.get_by_id(adjustment_id)
        if not adj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adjustment not found",
            )
        if adj.status != AdjustmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Adjustment is already {adj.status.value}",
            )

        adj.status = AdjustmentStatus.REJECTED
        adj.approved_by = reviewer_id
        adj.approved_at = datetime.now(timezone.utc)
        adj.rejection_reason = data.rejection_reason
        await self.session.flush()
        await self.session.refresh(adj)

        await self.audit.log(
            entity_type="OTBAdjustment",
            entity_id=adjustment_id,
            action=AuditAction.UPDATE,
            user_id=reviewer_id,
            description=f"Rejected adjustment: {data.rejection_reason}",
            season_id=adj.season_id,
        )

        return adj

    async def get_adjustments(
        self, season_id: UUID, skip: int = 0, limit: int = 100,
    ) -> tuple[list[OTBAdjustment], int]:
        """List adjustments for a season."""
        items = await self.adjustment_repo.get_by_season(season_id, skip, limit)
        total = await self.adjustment_repo.count_by_season(season_id)
        return items, total

    # ─── Internal Helpers ─────────────────────────────────────────────────

    async def _get_season(self, season_id: UUID) -> Season:
        season = await self.season_repo.get_by_id(season_id)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Season {season_id} not found",
            )
        return season

    async def _get_planned_otb_by_category_month(
        self, season_id: UUID, category_id: Optional[UUID] = None,
    ) -> dict[tuple, Decimal]:
        """Sum OTB plan rows → {(category_id, month): planned_otb}."""
        query = (
            select(
                OTBPlan.category_id,
                OTBPlan.month,
                func.sum(OTBPlan.approved_spend_limit).label("planned_otb"),
            )
            .where(OTBPlan.season_id == season_id)
            .group_by(OTBPlan.category_id, OTBPlan.month)
        )
        if category_id:
            query = query.where(OTBPlan.category_id == category_id)

        result = await self.session.execute(query)
        return {
            (row.category_id, row.month): row.planned_otb or Decimal("0.00")
            for row in result.all()
        }

    async def _get_consumed_otb_by_category_month(
        self, season_id: UUID, category_id: Optional[UUID] = None,
    ) -> dict[tuple, Decimal]:
        """Sum active PO values → {(category_id, month): consumed}."""
        # Active PO statuses (not cancelled)
        active_statuses = [
            POStatus.DRAFT, POStatus.SUBMITTED, POStatus.CONFIRMED,
            POStatus.SHIPPED, POStatus.PARTIAL, POStatus.COMPLETE,
        ]
        query = (
            select(
                PurchaseOrder.category_id,
                func.strftime("%Y-%m-01", PurchaseOrder.order_date).label("month"),
                func.sum(PurchaseOrder.po_value).label("consumed"),
            )
            .where(
                PurchaseOrder.season_id == season_id,
                PurchaseOrder.status.in_(active_statuses),
                PurchaseOrder.order_date.is_not(None),
            )
            .group_by(PurchaseOrder.category_id, func.strftime("%Y-%m-01", PurchaseOrder.order_date))
        )
        if category_id:
            query = query.where(PurchaseOrder.category_id == category_id)

        result = await self.session.execute(query)
        consumed = {}
        for row in result.all():
            month_date = row.month.date() if hasattr(row.month, 'date') else row.month
            if month_date:
                consumed[(row.category_id, month_date)] = row.consumed or Decimal("0.00")
        return consumed

    async def _get_approved_adjustment_totals(
        self, season_id: UUID, category_id: Optional[UUID] = None,
    ) -> dict[tuple, Decimal]:
        """Get net adjustments → {("from"|"to", category_id): total_amount}."""
        adjustments = {}

        # Outgoing adjustments (from)
        from_query = (
            select(
                OTBAdjustment.from_category_id,
                func.sum(OTBAdjustment.amount).label("total"),
            )
            .where(
                OTBAdjustment.season_id == season_id,
                OTBAdjustment.status == AdjustmentStatus.APPROVED,
                OTBAdjustment.from_category_id.is_not(None),
            )
            .group_by(OTBAdjustment.from_category_id)
        )
        if category_id:
            from_query = from_query.where(OTBAdjustment.from_category_id == category_id)
        result = await self.session.execute(from_query)
        for row in result.all():
            adjustments[("from", row.from_category_id)] = row.total or Decimal("0.00")

        # Incoming adjustments (to)
        to_query = (
            select(
                OTBAdjustment.to_category_id,
                func.sum(OTBAdjustment.amount).label("total"),
            )
            .where(
                OTBAdjustment.season_id == season_id,
                OTBAdjustment.status == AdjustmentStatus.APPROVED,
                OTBAdjustment.to_category_id.is_not(None),
            )
            .group_by(OTBAdjustment.to_category_id)
        )
        if category_id:
            to_query = to_query.where(OTBAdjustment.to_category_id == category_id)
        result = await self.session.execute(to_query)
        for row in result.all():
            adjustments[("to", row.to_category_id)] = row.total or Decimal("0.00")

        return adjustments

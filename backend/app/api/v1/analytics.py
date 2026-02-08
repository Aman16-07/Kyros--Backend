"""Analytics API endpoints for dashboard and reporting.

READ-ONLY ANALYTICS VIEW
These endpoints provide analytics and reporting for seasons.
Available for all seasons, but LOCKED seasons are fully read-only.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DBSession
from app.services.analytics_service import AnalyticsService
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.services.plan_service import SeasonPlanService
from app.services.otb_service import OTBService
from app.services.range_intent_service import RangeIntentService
from app.services.po_ingest_service import POIngestService
from app.services.grn_ingest_service import GRNIngestService
from app.schemas.plan import SeasonPlanResponse
from app.schemas.otb import OTBPlanResponse
from app.schemas.range_intent import RangeIntentResponse
from app.schemas.po import PurchaseOrderResponse
from app.schemas.grn import GRNRecordResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/read-only-view/{season_id}",
    summary="Get complete read-only analytics view",
    description="""
    Get the complete read-only analytics view for a LOCKED season.
    
    This is the final step in the workflow - after a season is locked,
    this endpoint provides comprehensive analytics including:
    - Season Plan vs Actuals
    - OTB vs Spend
    - PO vs Plan
    - GRN vs Plan
    
    NOTE: Season must be LOCKED for full analytics. Other statuses
    will return partial data based on completed workflow steps.
    """,
)
async def get_readonly_analytics_view(
    season_id: UUID,
    db: DBSession,
) -> dict:
    """Get complete read-only analytics view for a locked season."""
    orchestrator = WorkflowOrchestrator(db)
    analytics = AnalyticsService(db)
    
    # Get workflow status
    workflow_status = await orchestrator.get_workflow_status(season_id)
    
    # Get all analytics data
    dashboard = await analytics.get_dashboard_overview(season_id)
    budget_vs_actual = await analytics.get_budget_vs_actual(season_id)
    category_breakdown = await analytics.get_category_breakdown(season_id)
    cluster_summary = await analytics.get_cluster_summary(season_id)
    po_status = await analytics.get_po_status_breakdown(season_id)
    price_band = await analytics.get_price_band_analysis(season_id)
    
    return {
        "season_id": str(season_id),
        "season_code": workflow_status.get("season_code"),
        "season_name": workflow_status.get("season_name"),
        "status": workflow_status.get("current_status"),
        "is_locked": workflow_status.get("current_status") == "locked",
        "is_editable": workflow_status.get("is_editable", True),
        "analytics": {
            "season_plan_vs_actuals": {
                "planned_sales": dashboard.get("plans", {}).get("planned_sales"),
                "actual_received": dashboard.get("grn", {}).get("total_received"),
                "variance": (
                    dashboard.get("plans", {}).get("planned_sales", 0) -
                    dashboard.get("grn", {}).get("total_received", 0)
                ),
            },
            "otb_vs_spend": budget_vs_actual,
            "po_vs_plan": {
                "total_budget": dashboard.get("otb", {}).get("total_budget"),
                "total_po_value": dashboard.get("purchase_orders", {}).get("total_value"),
                "budget_utilization": dashboard.get("purchase_orders", {}).get("budget_utilization"),
            },
            "grn_vs_plan": {
                "total_po_value": dashboard.get("purchase_orders", {}).get("total_value"),
                "total_received": dashboard.get("grn", {}).get("total_received"),
                "fulfillment_rate": dashboard.get("grn", {}).get("fulfillment_rate"),
            },
            "category_breakdown": category_breakdown,
            "cluster_summary": cluster_summary,
            "po_status": po_status,
            "price_band_analysis": price_band,
        },
        "workflow": workflow_status.get("workflow"),
    }


@router.get(
    "/complete-view/{season_id}",
    summary="Get complete season data with all records (READ-ONLY for locked seasons)",
    description="""
    Get the complete season data including:
    - Season plan records (all rows)
    - OTB plan limits (all rows)
    - Range intents (all rows)
    - Purchase orders with GRN status
    - PO vs Plan comparison
    - GRN vs Plan comparison
    
    This is the comprehensive read-only view requested for Phase 1.
    For LOCKED seasons, this represents the immutable final state.
    """,
)
async def get_complete_season_view(
    season_id: UUID,
    db: DBSession,
    include_details: bool = Query(True, description="Include all record details"),
    limit: int = Query(1000, ge=1, le=5000, description="Max records per category"),
) -> dict:
    """Get complete season data with all detail records."""
    orchestrator = WorkflowOrchestrator(db)
    analytics = AnalyticsService(db)
    
    # Get workflow status
    workflow_status = await orchestrator.get_workflow_status(season_id)
    is_locked = workflow_status.get("current_status") == "locked"
    
    # Get analytics summary
    dashboard = await analytics.get_dashboard_overview(season_id)
    
    result = {
        "season_id": str(season_id),
        "season_code": workflow_status.get("season_code"),
        "season_name": workflow_status.get("season_name"),
        "status": workflow_status.get("current_status"),
        "is_locked": is_locked,
        "is_editable": not is_locked,
        "message": "This season is LOCKED. All data is read-only and immutable." if is_locked else "Season is still editable until locked.",
        "summary": dashboard,
        "workflow": workflow_status.get("workflow"),
    }
    
    if include_details:
        # Get all season plan records
        plan_service = SeasonPlanService(db)
        plans, plan_total = await plan_service.get_plans_by_season(season_id, 0, limit)
        result["season_plans"] = {
            "total": plan_total,
            "records": [SeasonPlanResponse.model_validate(p).model_dump() for p in plans],
        }
        
        # Get all OTB records
        otb_service = OTBService(db)
        otb_plans, otb_total = await otb_service.get_otb_plans_by_season(season_id, 0, limit)
        result["otb_limits"] = {
            "total": otb_total,
            "records": [OTBPlanResponse.model_validate(o).model_dump() for o in otb_plans],
        }
        
        # Get all range intents
        range_service = RangeIntentService(db)
        range_intents, range_total = await range_service.get_range_intents_by_season(season_id, 0, limit)
        result["range_intents"] = {
            "total": range_total,
            "records": [RangeIntentResponse.model_validate(r).model_dump() for r in range_intents],
        }
        
        # Get all purchase orders
        po_service = POIngestService(db)
        pos, po_total = await po_service.get_purchase_orders(season_id=season_id, skip=0, limit=limit)
        result["purchase_orders"] = {
            "total": po_total,
            "records": [PurchaseOrderResponse.model_validate(po).model_dump() for po in pos],
        }
        
        # Get all GRN records for this season's POs
        grn_service = GRNIngestService(db)
        all_grns = []
        for po in pos:
            grns, _ = await grn_service.get_grn_records_by_po(po.id, 0, limit)
            all_grns.extend(grns)
        result["grn_records"] = {
            "total": len(all_grns),
            "records": [GRNRecordResponse.model_validate(g).model_dump() for g in all_grns],
        }
        
        # PO vs Plan comparison
        total_otb_budget = sum(o.approved_spend_limit for o in otb_plans)
        total_po_value = sum(po.po_value for po in pos)
        result["po_vs_plan"] = {
            "total_otb_budget": float(total_otb_budget),
            "total_po_value": float(total_po_value),
            "variance": float(total_otb_budget - total_po_value),
            "utilization_percent": float((total_po_value / total_otb_budget * 100) if total_otb_budget > 0 else 0),
        }
        
        # GRN vs Plan comparison
        total_received = sum(g.received_value for g in all_grns)
        result["grn_vs_plan"] = {
            "total_po_value": float(total_po_value),
            "total_received": float(total_received),
            "variance": float(total_po_value - total_received),
            "fulfillment_percent": float((total_received / total_po_value * 100) if total_po_value > 0 else 0),
        }
    
    return result


@router.get(
    "/dashboard/{season_id}",
    summary="Get season dashboard overview",
)
async def get_dashboard(
    season_id: UUID,
    db: DBSession,
) -> dict:
    """
    Get the main dashboard overview for a season.
    
    Returns:
        - Budget vs Actual spend
        - PO fulfillment rates
        - Category breakdown
        - Monthly trends
    """
    service = AnalyticsService(db)
    return await service.get_dashboard_overview(season_id)


@router.get(
    "/budget-vs-actual/{season_id}",
    summary="Get budget vs actual analysis",
)
async def get_budget_vs_actual(
    season_id: UUID,
    db: DBSession,
    cluster_id: Optional[UUID] = Query(None, description="Filter by cluster"),
) -> dict:
    """
    Compare budgeted OTB vs actual PO spend.
    
    Returns monthly breakdown with:
        - OTB budget
        - Actual committed (PO value)
        - Actual received (GRN value)
        - Variance percentage
    """
    service = AnalyticsService(db)
    return await service.get_budget_vs_actual(season_id, cluster_id)


@router.get(
    "/category-breakdown/{season_id}",
    summary="Get category-level breakdown",
)
async def get_category_breakdown(
    season_id: UUID,
    db: DBSession,
    level: Optional[int] = Query(None, ge=1, le=4, description="Category depth"),
) -> dict:
    """
    Get spend breakdown by category.
    
    Returns:
        - Budget allocation per category
        - Actual spend per category
        - Variance analysis
    """
    service = AnalyticsService(db)
    return await service.get_category_breakdown(season_id, level)


@router.get(
    "/cluster-summary/{season_id}",
    summary="Get cluster-level summary",
)
async def get_cluster_summary(
    season_id: UUID,
    db: DBSession,
) -> dict:
    """
    Get summary metrics per cluster.
    
    Returns:
        - Total budget per cluster
        - Total committed per cluster
        - Total received per cluster
        - Location count per cluster
    """
    service = AnalyticsService(db)
    return await service.get_cluster_summary(season_id)


@router.get(
    "/location-performance/{season_id}",
    summary="Get location performance metrics",
)
async def get_location_performance(
    season_id: UUID,
    db: DBSession,
    cluster_id: Optional[UUID] = Query(None, description="Filter by cluster"),
    limit: int = Query(10, ge=1, le=100, description="Number of locations"),
) -> dict:
    """
    Get top/bottom performing locations by various metrics.
    
    Returns:
        - Top performing locations (by budget utilization)
        - Bottom performing locations
        - Fulfillment rates
    """
    service = AnalyticsService(db)
    return await service.get_location_performance(season_id, cluster_id, limit)


@router.get(
    "/po-status/{season_id}",
    summary="Get PO status breakdown",
)
async def get_po_status(
    season_id: UUID,
    db: DBSession,
) -> dict:
    """
    Get PO status breakdown.
    
    Returns:
        - POs by status
        - Fulfillment rate
        - Average lead time
        - Pending deliveries
    """
    service = AnalyticsService(db)
    return await service.get_po_status_breakdown(season_id)


@router.get(
    "/price-band-analysis/{season_id}",
    summary="Get price band analysis",
)
async def get_price_band_analysis(
    season_id: UUID,
    db: DBSession,
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
) -> dict:
    """
    Analyze price band distribution from range intent.
    
    Returns:
        - Price band mix per category
        - Core vs Fashion split
        - Budget allocation by price band
    """
    service = AnalyticsService(db)
    return await service.get_price_band_analysis(season_id, category_id)


@router.get(
    "/workflow-status",
    summary="Get workflow status summary",
)
async def get_workflow_status(
    db: DBSession,
) -> dict:
    """
    Get workflow status summary across all seasons.
    
    Returns:
        - Seasons by workflow state
        - Pending actions
        - Last state changes
    """
    service = AnalyticsService(db)
    return await service.get_workflow_status_summary()


@router.get(
    "/export/{season_id}",
    summary="Export season data",
)
async def export_season_data(
    season_id: UUID,
    db: DBSession,
    format: str = Query("json", pattern="^(json|csv)$", description="Export format"),
) -> dict:
    """
    Export complete season data for reporting.
    
    Returns comprehensive season data including:
        - Plans
        - OTB
        - Range Intent
        - POs
        - GRN Records
    """
    service = AnalyticsService(db)
    return await service.export_season_data(season_id, format)


@router.get(
    "/plan-vs-execution/{season_id}",
    summary="Get plan vs execution analysis",
    description="Compare planned quantities with actual purchased and received quantities",
)
async def get_plan_vs_execution(
    season_id: UUID,
    db: DBSession,
) -> dict:
    """
    Get plan vs execution analysis for Step 8 analytics.
    
    Returns:
        - Planned quantities per SKU/category
        - Purchased quantities (from POs)
        - Received quantities (from GRNs)
        - Variance analysis
    """
    service = AnalyticsService(db)
    return await service.get_plan_vs_execution(season_id)

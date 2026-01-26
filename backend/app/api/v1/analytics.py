"""Analytics API endpoints for dashboard and reporting."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.deps import DBSession
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


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

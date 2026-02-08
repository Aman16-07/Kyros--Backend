"""Analytics service - business intelligence and reporting."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cluster import Cluster
from app.models.grn import GRNRecord
from app.models.location import Location
from app.models.otb_plan import OTBPlan
from app.models.purchase_order import PurchaseOrder
from app.models.range_intent import RangeIntent
from app.models.season import Season
from app.models.season_plan import SeasonPlan
from app.models.workflow import SeasonWorkflow


class AnalyticsService:
    """Service for analytics and reporting."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_dashboard_overview(self, season_id: UUID) -> dict:
        """Get dashboard metrics for a season."""
        # Plan metrics
        plan_result = await self.session.execute(
            select(
                func.count(SeasonPlan.id).label("total_plans"),
                func.sum(SeasonPlan.planned_sales).label("total_planned_sales"),
                func.sum(SeasonPlan.planned_margin).label("total_planned_margin"),
                func.count(SeasonPlan.id).filter(SeasonPlan.approved == True).label("approved_plans"),
            ).where(SeasonPlan.season_id == season_id)
        )
        plan_row = plan_result.one()
        
        # OTB metrics
        otb_result = await self.session.execute(
            select(
                func.count(OTBPlan.id).label("total_otb"),
                func.sum(OTBPlan.approved_spend_limit).label("total_budget"),
            ).where(OTBPlan.season_id == season_id)
        )
        otb_row = otb_result.one()
        
        # PO metrics
        po_result = await self.session.execute(
            select(
                func.count(PurchaseOrder.id).label("total_pos"),
                func.sum(PurchaseOrder.po_value).label("total_po_value"),
            ).where(PurchaseOrder.season_id == season_id)
        )
        po_row = po_result.one()
        
        # GRN metrics (through POs)
        grn_result = await self.session.execute(
            select(
                func.count(GRNRecord.id).label("total_grns"),
                func.sum(GRNRecord.received_value).label("total_received"),
            ).join(PurchaseOrder, GRNRecord.po_id == PurchaseOrder.id)
            .where(PurchaseOrder.season_id == season_id)
        )
        grn_row = grn_result.one()
        
        # Range intent metrics
        range_result = await self.session.execute(
            select(
                func.count(RangeIntent.id).label("total_intents"),
                func.avg(RangeIntent.core_percent).label("avg_core_percent"),
                func.avg(RangeIntent.fashion_percent).label("avg_fashion_percent"),
            ).where(RangeIntent.season_id == season_id)
        )
        range_row = range_result.one()
        
        total_budget = otb_row.total_budget or Decimal("0.00")
        total_po_value = po_row.total_po_value or Decimal("0.00")
        
        return {
            "season_id": str(season_id),
            "plans": {
                "total": plan_row.total_plans or 0,
                "approved": plan_row.approved_plans or 0,
                "planned_sales": plan_row.total_planned_sales or Decimal("0.00"),
                "planned_margin": plan_row.total_planned_margin or Decimal("0.00"),
            },
            "otb": {
                "total": otb_row.total_otb or 0,
                "total_budget": total_budget,
            },
            "purchase_orders": {
                "total": po_row.total_pos or 0,
                "total_value": total_po_value,
                "budget_utilization": (
                    (total_po_value / total_budget * 100) if total_budget > 0 else Decimal("0.00")
                ),
            },
            "grn": {
                "total": grn_row.total_grns or 0,
                "total_received": grn_row.total_received or Decimal("0.00"),
                "fulfillment_rate": (
                    (grn_row.total_received / total_po_value * 100)
                    if total_po_value > 0 else Decimal("0.00")
                ),
            },
            "range_intent": {
                "total": range_row.total_intents or 0,
                "avg_core_percent": range_row.avg_core_percent or Decimal("0.00"),
                "avg_fashion_percent": range_row.avg_fashion_percent or Decimal("0.00"),
            },
        }
    
    async def get_budget_vs_actual(
        self,
        season_id: UUID,
        cluster_id: Optional[UUID] = None,
    ) -> dict:
        """Get budget vs actual spend by month."""
        # OTB budget by month
        otb_query = (
            select(
                OTBPlan.month,
                func.sum(OTBPlan.approved_spend_limit).label("budget"),
            )
            .where(OTBPlan.season_id == season_id)
        )
        
        if cluster_id:
            otb_query = otb_query.join(Location, OTBPlan.location_id == Location.id)
            otb_query = otb_query.where(Location.cluster_id == cluster_id)
        
        otb_by_month = await self.session.execute(
            otb_query.group_by(OTBPlan.month).order_by(OTBPlan.month)
        )
        
        budget_data = {row.month: row.budget for row in otb_by_month.all()}
        
        # Actual spend by month (from GRN)
        actual_query = (
            select(
                func.strftime("%Y-%m-01", GRNRecord.grn_date).label("month"),
                func.sum(GRNRecord.received_value).label("actual"),
            )
            .join(PurchaseOrder, GRNRecord.po_id == PurchaseOrder.id)
            .where(PurchaseOrder.season_id == season_id)
        )
        
        if cluster_id:
            actual_query = actual_query.join(Location, PurchaseOrder.location_id == Location.id)
            actual_query = actual_query.where(Location.cluster_id == cluster_id)
        
        actual_by_month = await self.session.execute(
            actual_query.group_by(func.strftime("%Y-%m-01", GRNRecord.grn_date))
        )
        
        actual_data = {}
        for row in actual_by_month.all():
            if row.month:
                # strftime returns string "YYYY-MM-01", convert to date for consistency
                from datetime import date as date_type
                if isinstance(row.month, str):
                    actual_data[date_type.fromisoformat(row.month)] = row.actual
                else:
                    actual_data[row.month.date() if hasattr(row.month, 'date') else row.month] = row.actual
        
        # Combine data
        all_months = set(budget_data.keys()) | {m for m in actual_data.keys() if m}
        
        monthly_data = [
            {
                "month": str(month),
                "budget": budget_data.get(month, Decimal("0.00")),
                "actual": actual_data.get(month, Decimal("0.00")),
                "variance": budget_data.get(month, Decimal("0.00")) - actual_data.get(month, Decimal("0.00")),
                "variance_percent": (
                    ((budget_data.get(month, Decimal("0.00")) - actual_data.get(month, Decimal("0.00"))) 
                     / budget_data.get(month, Decimal("1.00")) * 100)
                    if budget_data.get(month, Decimal("0.00")) > 0 else Decimal("0.00")
                ),
            }
            for month in sorted(m for m in all_months if m)
        ]
        
        return {
            "season_id": str(season_id),
            "cluster_id": str(cluster_id) if cluster_id else None,
            "monthly_data": monthly_data,
            "totals": {
                "total_budget": sum(d["budget"] for d in monthly_data),
                "total_actual": sum(d["actual"] for d in monthly_data),
                "total_variance": sum(d["variance"] for d in monthly_data),
            },
        }
    
    async def get_category_breakdown(
        self,
        season_id: UUID,
        level: Optional[int] = None,
    ) -> dict:
        """Get breakdown by category."""
        result = await self.session.execute(
            select(
                SeasonPlan.category_id,
                func.sum(SeasonPlan.planned_sales).label("planned_sales"),
                func.sum(SeasonPlan.planned_margin).label("planned_margin"),
            )
            .where(SeasonPlan.season_id == season_id)
            .group_by(SeasonPlan.category_id)
        )
        
        categories = [
            {
                "category_id": str(row.category_id),
                "planned_sales": row.planned_sales or Decimal("0.00"),
                "planned_margin": row.planned_margin or Decimal("0.00"),
            }
            for row in result.all()
        ]
        
        return {
            "season_id": str(season_id),
            "level": level,
            "categories": categories,
            "totals": {
                "total_planned_sales": sum(c["planned_sales"] for c in categories),
                "total_planned_margin": sum(c["planned_margin"] for c in categories),
            },
        }
    
    async def get_cluster_summary(self, season_id: UUID) -> dict:
        """Get summary metrics per cluster."""
        # Get clusters with their stats
        result = await self.session.execute(
            select(
                Cluster.id,
                Cluster.name,
                func.count(Location.id.distinct()).label("location_count"),
                func.sum(OTBPlan.approved_spend_limit).label("total_budget"),
            )
            .join(Location, Location.cluster_id == Cluster.id)
            .outerjoin(OTBPlan, (OTBPlan.location_id == Location.id) & (OTBPlan.season_id == season_id))
            .group_by(Cluster.id, Cluster.name)
        )
        
        clusters = []
        for row in result.all():
            # Get PO value for this cluster
            po_result = await self.session.execute(
                select(func.sum(PurchaseOrder.po_value))
                .join(Location, PurchaseOrder.location_id == Location.id)
                .where(
                    (PurchaseOrder.season_id == season_id) &
                    (Location.cluster_id == row.id)
                )
            )
            total_committed = po_result.scalar() or Decimal("0.00")
            
            # Get GRN value for this cluster
            grn_result = await self.session.execute(
                select(func.sum(GRNRecord.received_value))
                .join(PurchaseOrder, GRNRecord.po_id == PurchaseOrder.id)
                .join(Location, PurchaseOrder.location_id == Location.id)
                .where(
                    (PurchaseOrder.season_id == season_id) &
                    (Location.cluster_id == row.id)
                )
            )
            total_received = grn_result.scalar() or Decimal("0.00")
            
            clusters.append({
                "cluster_id": str(row.id),
                "cluster_name": row.name,
                "location_count": row.location_count or 0,
                "total_budget": row.total_budget or Decimal("0.00"),
                "total_committed": total_committed,
                "total_received": total_received,
            })
        
        return {
            "season_id": str(season_id),
            "clusters": clusters,
        }
    
    async def get_location_performance(
        self,
        season_id: UUID,
        cluster_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> dict:
        """Get location performance metrics."""
        query = (
            select(
                Location.id,
                Location.name,
                func.sum(OTBPlan.approved_spend_limit).label("budget"),
            )
            .join(OTBPlan, (OTBPlan.location_id == Location.id) & (OTBPlan.season_id == season_id))
        )
        
        if cluster_id:
            query = query.where(Location.cluster_id == cluster_id)
        
        query = query.group_by(Location.id, Location.name)
        
        result = await self.session.execute(query)
        
        locations = []
        for row in result.all():
            # Get actual spend
            actual_result = await self.session.execute(
                select(func.sum(GRNRecord.received_value))
                .join(PurchaseOrder, GRNRecord.po_id == PurchaseOrder.id)
                .where(
                    (PurchaseOrder.season_id == season_id) &
                    (PurchaseOrder.location_id == row.id)
                )
            )
            actual = actual_result.scalar() or Decimal("0.00")
            budget = row.budget or Decimal("0.00")
            
            locations.append({
                "location_id": str(row.id),
                "location_name": row.name,
                "budget": budget,
                "actual": actual,
                "utilization": (actual / budget * 100) if budget > 0 else Decimal("0.00"),
            })
        
        # Sort by utilization
        locations.sort(key=lambda x: x["utilization"], reverse=True)
        
        return {
            "season_id": str(season_id),
            "cluster_id": str(cluster_id) if cluster_id else None,
            "top_performers": locations[:limit],
            "bottom_performers": list(reversed(locations[-limit:])) if len(locations) > limit else [],
        }
    
    async def get_po_status_breakdown(self, season_id: UUID) -> dict:
        """Get PO status breakdown."""
        # Count POs
        po_count = await self.session.execute(
            select(func.count(PurchaseOrder.id))
            .where(PurchaseOrder.season_id == season_id)
        )
        total_pos = po_count.scalar() or 0
        
        # Total PO value
        po_value = await self.session.execute(
            select(func.sum(PurchaseOrder.po_value))
            .where(PurchaseOrder.season_id == season_id)
        )
        total_value = po_value.scalar() or Decimal("0.00")
        
        # Total received
        received = await self.session.execute(
            select(func.sum(GRNRecord.received_value))
            .join(PurchaseOrder, GRNRecord.po_id == PurchaseOrder.id)
            .where(PurchaseOrder.season_id == season_id)
        )
        total_received = received.scalar() or Decimal("0.00")
        
        # Count POs with full delivery
        full_delivery = await self.session.execute(
            select(func.count(PurchaseOrder.id.distinct()))
            .join(GRNRecord, GRNRecord.po_id == PurchaseOrder.id)
            .where(PurchaseOrder.season_id == season_id)
            .group_by(PurchaseOrder.id)
            .having(func.sum(GRNRecord.received_value) >= PurchaseOrder.po_value)
        )
        fully_received_count = len(full_delivery.all())
        
        return {
            "season_id": str(season_id),
            "total_pos": total_pos,
            "total_value": total_value,
            "total_received": total_received,
            "pending_value": total_value - total_received,
            "fulfillment_rate": (total_received / total_value * 100) if total_value > 0 else Decimal("0.00"),
            "fully_received_count": fully_received_count,
            "pending_delivery_count": total_pos - fully_received_count,
        }
    
    async def get_price_band_analysis(
        self,
        season_id: UUID,
        category_id: Optional[UUID] = None,
    ) -> dict:
        """Analyze price band distribution from range intent."""
        query = select(RangeIntent).where(RangeIntent.season_id == season_id)
        
        if category_id:
            query = query.where(RangeIntent.category_id == category_id)
        
        result = await self.session.execute(query)
        intents = result.scalars().all()
        
        # Aggregate price band data
        price_bands = {}
        total_core = Decimal("0.00")
        total_fashion = Decimal("0.00")
        
        for intent in intents:
            total_core += intent.core_percent or Decimal("0.00")
            total_fashion += intent.fashion_percent or Decimal("0.00")
            
            if intent.price_band_mix:
                for band, value in intent.price_band_mix.items():
                    if band not in price_bands:
                        price_bands[band] = Decimal("0.00")
                    price_bands[band] += Decimal(str(value))
        
        count = len(intents) or 1
        
        return {
            "season_id": str(season_id),
            "category_id": str(category_id) if category_id else None,
            "intent_count": len(intents),
            "avg_core_percent": total_core / count,
            "avg_fashion_percent": total_fashion / count,
            "price_band_distribution": {
                band: value / count for band, value in price_bands.items()
            },
        }
    
    async def get_workflow_status_summary(self) -> dict:
        """Get workflow status summary across all seasons."""
        result = await self.session.execute(
            select(
                Season.status,
                func.count(Season.id).label("count"),
            )
            .group_by(Season.status)
        )
        
        status_counts = {str(row.status.value): row.count for row in result.all()}
        
        # Get recent workflow changes
        recent_result = await self.session.execute(
            select(SeasonWorkflow)
            .order_by(SeasonWorkflow.updated_at.desc())
            .limit(10)
        )
        recent_changes = [
            {
                "season_id": str(wf.season_id),
                "locked": wf.locked,
                "otb_uploaded": wf.otb_uploaded,
                "range_uploaded": wf.range_uploaded,
                "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
            }
            for wf in recent_result.scalars().all()
        ]
        
        return {
            "by_status": status_counts,
            "total_seasons": sum(status_counts.values()),
            "recent_changes": recent_changes,
        }
    
    async def export_season_data(
        self,
        season_id: UUID,
        format: str = "json",
    ) -> dict:
        """Export complete season data."""
        # Gather all data
        dashboard = await self.get_dashboard_overview(season_id)
        budget_actual = await self.get_budget_vs_actual(season_id)
        category_breakdown = await self.get_category_breakdown(season_id)
        cluster_summary = await self.get_cluster_summary(season_id)
        po_status = await self.get_po_status_breakdown(season_id)
        
        export_data = {
            "season_id": str(season_id),
            "export_format": format,
            "dashboard": dashboard,
            "budget_vs_actual": budget_actual,
            "category_breakdown": category_breakdown,
            "cluster_summary": cluster_summary,
            "po_status": po_status,
        }
        
        return export_data

    async def get_plan_vs_execution(self, season_id: UUID) -> dict:
        """
        Get plan vs execution analysis.
        
        Compares planned quantities from season plans with actual
        purchased (POs) and received (GRNs) quantities by category.
        """
        from app.models.category import Category
        
        # Get planned values by category from season plans
        plans_result = await self.session.execute(
            select(
                Category.id.label("category_id"),
                Category.name.label("category"),
                func.sum(SeasonPlan.planned_sales).label("planned_qty"),
            )
            .join(Category, SeasonPlan.category_id == Category.id)
            .where(SeasonPlan.season_id == season_id)
            .group_by(Category.id, Category.name)
        )
        plans_by_category = {str(row.category_id): {
            "category": row.category,
            "planned_qty": float(row.planned_qty or 0),
        } for row in plans_result.all()}
        
        # Get PO values by category
        po_result = await self.session.execute(
            select(
                Category.id.label("category_id"),
                func.sum(PurchaseOrder.po_value).label("purchased_qty"),
            )
            .join(Category, PurchaseOrder.category_id == Category.id)
            .where(PurchaseOrder.season_id == season_id)
            .group_by(Category.id)
        )
        po_by_category = {str(row.category_id): float(row.purchased_qty or 0) 
                          for row in po_result.all()}
        
        # Get GRN values by category (through POs)
        grn_result = await self.session.execute(
            select(
                PurchaseOrder.category_id,
                func.sum(GRNRecord.received_value).label("received_qty"),
            )
            .join(PurchaseOrder, GRNRecord.po_id == PurchaseOrder.id)
            .where(PurchaseOrder.season_id == season_id)
            .group_by(PurchaseOrder.category_id)
        )
        grn_by_category = {str(row.category_id): float(row.received_qty or 0) 
                           for row in grn_result.all()}
        
        # Combine into items
        items = []
        for cat_id, plan_data in plans_by_category.items():
            planned = plan_data["planned_qty"]
            purchased = po_by_category.get(cat_id, 0)
            received = grn_by_category.get(cat_id, 0)
            variance = received - planned
            
            items.append({
                "sku": f"CAT-{cat_id[:8]}",  # Use category ID as SKU for now
                "category": plan_data["category"],
                "planned_qty": planned,
                "purchased_qty": purchased,
                "received_qty": received,
                "variance": variance,
                "variance_explanation": (
                    "Within tolerance" if abs(variance) < 0.01 * planned else
                    "Over supplied" if variance > 0 else
                    "Under supplied"
                ) if planned > 0 else "No plan",
            })
        
        return {
            "season_id": str(season_id),
            "items": items,
            "summary": {
                "total_planned": sum(i["planned_qty"] for i in items),
                "total_purchased": sum(i["purchased_qty"] for i in items),
                "total_received": sum(i["received_qty"] for i in items),
                "categories_count": len(items),
            },
        }

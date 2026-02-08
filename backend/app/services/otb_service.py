"""OTB Plan service - business logic for OTB plans.

OTB Formula: Planned Sales + Planned Closing Stock - Opening Stock - On Order
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workflow_guard import WorkflowGuard
from app.models.otb_plan import OTBPlan
from app.models.season import SeasonStatus
from app.repositories.otb_repo import OTBPlanRepository
from app.schemas.otb import OTBPlanCreate, OTBPlanUpdate, OTBSummary
from app.services.audit_service import AuditService


class OTBService:
    """Service for OTB plan business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OTBPlanRepository(session)
        self.guard = WorkflowGuard(session)
        self.audit = AuditService(session)
    
    @staticmethod
    def calculate_otb(
        planned_sales: Decimal,
        planned_closing_stock: Decimal,
        opening_stock: Decimal,
        on_order: Decimal,
    ) -> Decimal:
        """
        Calculate OTB using the formula:
        OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order
        """
        return planned_sales + planned_closing_stock - opening_stock - on_order
    
    async def create_otb_plan(self, data: OTBPlanCreate) -> OTBPlan:
        """Create a new OTB plan with calculated approved_spend_limit."""
        await self.guard.can_upload_otb(data.season_id)
        
        # Check for duplicate
        existing = await self.repo.get_by_composite_key(
            data.season_id,
            data.location_id,
            data.category_id,
            data.month,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="OTB plan already exists for this combination",
            )
        
        # Calculate OTB using formula
        approved_spend_limit = self.calculate_otb(
            data.planned_sales,
            data.planned_closing_stock,
            data.opening_stock,
            data.on_order,
        )
        
        plan = await self.repo.create(
            season_id=data.season_id,
            location_id=data.location_id,
            category_id=data.category_id,
            month=data.month.replace(day=1),  # Ensure first of month
            planned_sales=data.planned_sales,
            planned_closing_stock=data.planned_closing_stock,
            opening_stock=data.opening_stock,
            on_order=data.on_order,
            approved_spend_limit=approved_spend_limit,
            uploaded_by=data.uploaded_by,
        )
        
        return plan
    
    async def bulk_create_otb_plans(
        self,
        plans: list[OTBPlanCreate],
    ) -> list[OTBPlan]:
        """Bulk create OTB plans with calculated OTB values."""
        if not plans:
            return []
        
        await self.guard.can_upload_otb(plans[0].season_id)
        
        created_plans = []
        for plan_data in plans:
            # Calculate OTB using formula
            approved_spend_limit = self.calculate_otb(
                plan_data.planned_sales,
                plan_data.planned_closing_stock,
                plan_data.opening_stock,
                plan_data.on_order,
            )
            
            # Check for duplicate
            existing = await self.repo.get_by_composite_key(
                plan_data.season_id,
                plan_data.location_id,
                plan_data.category_id,
                plan_data.month,
            )
            
            if existing:
                # Update existing
                existing.planned_sales = plan_data.planned_sales
                existing.planned_closing_stock = plan_data.planned_closing_stock
                existing.opening_stock = plan_data.opening_stock
                existing.on_order = plan_data.on_order
                existing.approved_spend_limit = approved_spend_limit
                created_plans.append(existing)
            else:
                plan = await self.repo.create(
                    season_id=plan_data.season_id,
                    location_id=plan_data.location_id,
                    category_id=plan_data.category_id,
                    month=plan_data.month.replace(day=1),
                    planned_sales=plan_data.planned_sales,
                    planned_closing_stock=plan_data.planned_closing_stock,
                    opening_stock=plan_data.opening_stock,
                    on_order=plan_data.on_order,
                    approved_spend_limit=approved_spend_limit,
                    uploaded_by=plan_data.uploaded_by,
                )
                created_plans.append(plan)
        
        # Update workflow to mark OTB as uploaded
        await self.guard.update_workflow_step(
            plans[0].season_id,
            "otb_uploaded",
            SeasonStatus.OTB_UPLOADED,
        )
        
        # Audit log the bulk upload
        await self.audit.log_upload(
            entity_type="OTBPlan",
            entity_id=plans[0].season_id,
            user_id=plans[0].uploaded_by,
            record_count=len(created_plans),
            description=f"Bulk uploaded {len(created_plans)} OTB plans",
            season_id=plans[0].season_id,
        )
        
        return created_plans
    
    async def get_otb_plan(self, plan_id: UUID) -> OTBPlan:
        """Get an OTB plan by ID."""
        plan = await self.repo.get_with_details(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OTB plan not found",
            )
        return plan
    
    async def get_otb_plans_by_season(
        self,
        season_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[OTBPlan], int]:
        """Get OTB plans for a season."""
        plans = await self.repo.get_by_season(season_id, skip, limit)
        total = await self.repo.count(season_id=season_id)
        return plans, total
    
    async def get_otb_summary(self, season_id: UUID) -> list[OTBSummary]:
        """Get OTB summary by month."""
        summary_data = await self.repo.get_total_spend_by_month(season_id)
        return [
            OTBSummary(
                month=item["month"],
                total_spend_limit=item["total_spend_limit"],
                location_count=item["location_count"],
                category_count=item["category_count"],
            )
            for item in summary_data
        ]
    
    async def update_otb_plan(
        self,
        plan_id: UUID,
        data: OTBPlanUpdate,
        user_id: Optional[UUID] = None,
    ) -> OTBPlan:
        """Update an OTB plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OTB plan not found",
            )
        
        # Check OTB is mutable (not locked AND workflow has not progressed past OTB upload)
        await self.guard.check_otb_is_mutable(plan.season_id)
        
        # Capture old data for audit
        old_data = {
            "planned_sales": float(plan.planned_sales) if plan.planned_sales else None,
            "approved_spend_limit": float(plan.approved_spend_limit) if plan.approved_spend_limit else None,
        }
        
        update_data = data.model_dump(exclude_unset=True)
        updated_plan = await self.repo.update(plan_id, **update_data)
        
        # Audit log the update
        await self.audit.log_update(
            entity_type="OTBPlan",
            entity_id=plan_id,
            user_id=user_id,
            old_data=old_data,
            new_data=update_data,
            season_id=plan.season_id,
        )
        
        return updated_plan
    
    async def delete_otb_plan(self, plan_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete an OTB plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OTB plan not found",
            )
        
        # Check OTB is mutable (not locked AND workflow has not progressed past OTB upload)
        await self.guard.check_otb_is_mutable(plan.season_id)
        
        # Capture old data for audit
        old_data = {
            "id": str(plan.id),
            "season_id": str(plan.season_id),
            "month": plan.month.isoformat() if plan.month else None,
        }
        
        result = await self.repo.delete(plan_id)
        
        # Audit log the deletion
        await self.audit.log_delete(
            entity_type="OTBPlan",
            entity_id=plan_id,
            user_id=user_id,
            old_data=old_data,
            season_id=plan.season_id,
        )
        
        return result

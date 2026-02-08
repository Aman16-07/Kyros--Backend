"""Season Plan service - business logic for season plans."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workflow_guard import WorkflowGuard
from app.models.audit_log import AuditAction
from app.models.season import SeasonStatus
from app.models.season_plan import SeasonPlan
from app.repositories.plan_repo import SeasonPlanRepository
from app.repositories.season_repo import SeasonRepository
from app.schemas.plan import SeasonPlanCreate, SeasonPlanUpdate
from app.services.audit_service import AuditService


class SeasonPlanService:
    """Service for season plan business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SeasonPlanRepository(session)
        self.season_repo = SeasonRepository(session)
        self.guard = WorkflowGuard(session)
        self.audit = AuditService(session)
    
    async def create_plan(self, data: SeasonPlanCreate) -> SeasonPlan:
        """Create a new season plan."""
        # Check workflow allows plan upload
        await self.guard.can_upload_plan(data.season_id)
        
        # Get next version if not specified
        if data.version == 1:
            version = await self.repo.get_next_version(
                data.season_id,
                data.location_id,
                data.category_id,
            )
        else:
            version = data.version
        
        plan = await self.repo.create(
            season_id=data.season_id,
            location_id=data.location_id,
            category_id=data.category_id,
            sku_id=data.sku_id,
            planned_sales=data.planned_sales,
            planned_margin=data.planned_margin,
            planned_units=data.planned_units,
            inventory_turns=data.inventory_turns,
            ly_sales=data.ly_sales,
            lly_sales=data.lly_sales,
            version=version,
            uploaded_by=data.uploaded_by,
            approved=data.approved,
        )
        
        # Audit log the creation
        await self.audit.log_create(
            entity_type="SeasonPlan",
            entity_id=plan.id,
            user_id=data.uploaded_by,
            new_data={
                "season_id": str(data.season_id),
                "location_id": str(data.location_id),
                "category_id": str(data.category_id) if data.category_id else None,
                "planned_sales": float(data.planned_sales) if data.planned_sales else None,
                "planned_margin": float(data.planned_margin) if data.planned_margin else None,
                "version": version,
            },
            season_id=data.season_id,
        )
        
        return plan
    
    async def bulk_create_plans(
        self,
        plans: list[SeasonPlanCreate],
    ) -> list[SeasonPlan]:
        """Bulk create season plans."""
        if not plans:
            return []
        
        # Check workflow for first plan's season
        await self.guard.can_upload_plan(plans[0].season_id)
        
        created_plans = []
        for plan_data in plans:
            version = await self.repo.get_next_version(
                plan_data.season_id,
                plan_data.location_id,
                plan_data.category_id,
            )
            
            plan = await self.repo.create(
                season_id=plan_data.season_id,
                location_id=plan_data.location_id,
                category_id=plan_data.category_id,
                sku_id=plan_data.sku_id,
                planned_sales=plan_data.planned_sales,
                planned_margin=plan_data.planned_margin,
                planned_units=plan_data.planned_units,
                inventory_turns=plan_data.inventory_turns,
                ly_sales=plan_data.ly_sales,
                lly_sales=plan_data.lly_sales,
                version=version,
                uploaded_by=plan_data.uploaded_by,
                approved=plan_data.approved,
            )
            created_plans.append(plan)
        
        # Update workflow
        await self.guard.update_workflow_step(
            plans[0].season_id,
            "plan_uploaded",
            SeasonStatus.PLAN_UPLOADED,
        )
        
        # Audit log the bulk upload
        await self.audit.log_upload(
            entity_type="SeasonPlan",
            entity_id=plans[0].season_id,  # Use season_id as reference
            user_id=plans[0].uploaded_by,
            record_count=len(created_plans),
            description=f"Bulk uploaded {len(created_plans)} season plans",
            season_id=plans[0].season_id,
        )
        
        return created_plans
    
    async def get_plan(self, plan_id: UUID) -> SeasonPlan:
        """Get a plan by ID."""
        plan = await self.repo.get_with_details(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season plan not found",
            )
        return plan
    
    async def get_plans_by_season(
        self,
        season_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[SeasonPlan], int]:
        """Get plans for a season."""
        plans = await self.repo.get_by_season(season_id, skip, limit)
        total = await self.repo.count(season_id=season_id)
        return plans, total
    
    async def update_plan(
        self,
        plan_id: UUID,
        data: SeasonPlanUpdate,
        user_id: Optional[UUID] = None,
    ) -> SeasonPlan:
        """Update a season plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season plan not found",
            )
        
        # Check plan is mutable (not locked, not approved, workflow has not progressed past plan upload)
        await self.guard.check_plan_is_mutable(
            plan.season_id, 
            plan_id=plan_id, 
            is_approved=plan.approved
        )
        
        # Capture old data for audit
        old_data = {
            "planned_sales": float(plan.planned_sales) if plan.planned_sales else None,
            "planned_margin": float(plan.planned_margin) if plan.planned_margin else None,
            "approved": plan.approved,
        }
        
        update_data = data.model_dump(exclude_unset=True)
        updated_plan = await self.repo.update(plan_id, **update_data)
        
        # Audit log the update
        await self.audit.log_update(
            entity_type="SeasonPlan",
            entity_id=plan_id,
            user_id=user_id,
            old_data=old_data,
            new_data=update_data,
            season_id=plan.season_id,
        )
        
        return updated_plan
    
    async def delete_plan(self, plan_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete a season plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season plan not found",
            )
        
        # Check plan is mutable (not locked, not approved, workflow has not progressed past plan upload)
        await self.guard.check_plan_is_mutable(
            plan.season_id, 
            plan_id=plan_id, 
            is_approved=plan.approved
        )
        
        # Capture old data for audit
        old_data = {
            "id": str(plan.id),
            "season_id": str(plan.season_id),
            "location_id": str(plan.location_id),
            "planned_sales": float(plan.planned_sales) if plan.planned_sales else None,
        }
        
        result = await self.repo.delete(plan_id)
        
        # Audit log the deletion
        await self.audit.log_delete(
            entity_type="SeasonPlan",
            entity_id=plan_id,
            user_id=user_id,
            old_data=old_data,
            season_id=plan.season_id,
        )
        
        return result
    
    async def approve_plans(
        self,
        plan_ids: list[UUID],
        approved: bool = True,
        user_id: Optional[UUID] = None,
    ) -> int:
        """Approve plans. NOTE: Once approved, plans become IMMUTABLE and cannot be un-approved."""
        # Verify all plans exist and are mutable
        for plan_id in plan_ids:
            plan = await self.repo.get_by_id(plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan {plan_id} not found",
                )
            
            # If trying to un-approve an already approved plan, reject
            if not approved and plan.approved:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Plan {plan_id} is already approved and cannot be un-approved. Approved records are immutable.",
                )
            
            # Check plan is mutable (not locked AND workflow has not progressed past plan upload)
            # Don't check is_approved here since we're specifically approving
            await self.guard.check_plan_is_mutable(plan.season_id)
        
        count = await self.repo.approve_plans(plan_ids, approved)
        
        # Audit log the approval
        if plan_ids:
            first_plan = await self.repo.get_by_id(plan_ids[0])
            if first_plan:
                await self.audit.log(
                    entity_type="SeasonPlan",
                    entity_id=first_plan.season_id,
                    action=AuditAction.APPROVE,
                    user_id=user_id,
                    new_data={"plan_ids": [str(pid) for pid in plan_ids], "approved": approved},
                    description=f"{'Approved' if approved else 'Rejected'} {count} season plans",
                    season_id=first_plan.season_id,
                )
        
        return count

"""Season Plan service - business logic for season plans."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workflow_guard import WorkflowGuard
from app.models.season import SeasonStatus
from app.models.season_plan import SeasonPlan
from app.repositories.plan_repo import SeasonPlanRepository
from app.repositories.season_repo import SeasonRepository
from app.schemas.plan import SeasonPlanCreate, SeasonPlanUpdate


class SeasonPlanService:
    """Service for season plan business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SeasonPlanRepository(session)
        self.season_repo = SeasonRepository(session)
        self.guard = WorkflowGuard(session)
    
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
            planned_sales=data.planned_sales,
            planned_margin=data.planned_margin,
            inventory_turns=data.inventory_turns,
            version=version,
            uploaded_by=data.uploaded_by,
            approved=data.approved,
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
                planned_sales=plan_data.planned_sales,
                planned_margin=plan_data.planned_margin,
                inventory_turns=plan_data.inventory_turns,
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
    ) -> SeasonPlan:
        """Update a season plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season plan not found",
            )
        
        # Check not locked
        await self.guard.check_not_locked(plan.season_id)
        
        update_data = data.model_dump(exclude_unset=True)
        updated_plan = await self.repo.update(plan_id, **update_data)
        
        return updated_plan
    
    async def delete_plan(self, plan_id: UUID) -> bool:
        """Delete a season plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season plan not found",
            )
        
        await self.guard.check_not_locked(plan.season_id)
        
        return await self.repo.delete(plan_id)
    
    async def approve_plans(
        self,
        plan_ids: list[UUID],
        approved: bool = True,
    ) -> int:
        """Approve or reject plans."""
        # Verify all plans exist and are not locked
        for plan_id in plan_ids:
            plan = await self.repo.get_by_id(plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan {plan_id} not found",
                )
            await self.guard.check_not_locked(plan.season_id)
        
        return await self.repo.approve_plans(plan_ids, approved)

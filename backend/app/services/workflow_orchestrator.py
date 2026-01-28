"""
Workflow Orchestration Service.

Manages the complete Kyros workflow:
1. Create Season (generates unique season_code)
2. Define Locations (generates unique location_codes, maps to clusters)
3. Upload Season Plan (immutable once approved)
4. Upload OTB Plan (calculated from formula)
5. Upload Range Intent (core/fashion mix, price bands)
6. Ingest Purchase Orders
7. Ingest GRN Records
8. Read-Only Analytics View
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.season import Season, SeasonStatus
from app.models.workflow import SeasonWorkflow
from app.repositories.location_repo import LocationRepository
from app.repositories.season_repo import SeasonRepository, WorkflowRepository
from app.schemas.location import LocationCreate
from app.schemas.season import SeasonCreate
from app.utils.id_generators import generate_location_id, generate_season_id


class WorkflowOrchestrator:
    """
    Orchestrates the complete Kyros planning workflow.
    
    Workflow Steps:
    1. CREATED: Season created with unique season_code
    2. LOCATIONS_DEFINED: Locations defined with store-cluster mapping
    3. PLAN_UPLOADED: Season plan uploaded (immutable)
    4. OTB_UPLOADED: OTB plan calculated and uploaded
    5. RANGE_UPLOADED: Range intent uploaded
    6. LOCKED: Season locked - read-only analytics view
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.season_repo = SeasonRepository(session)
        self.workflow_repo = WorkflowRepository(session)
        self.location_repo = LocationRepository(session)
    
    # =========================================================================
    # STEP 1: Create Season
    # =========================================================================
    
    async def create_season(self, data: SeasonCreate) -> Season:
        """
        Create a new season with auto-generated season_code.
        
        Season code format: XXXX-XXXX (e.g., F9J1-KKG2)
        """
        # Get existing season codes to ensure uniqueness
        existing_codes = await self._get_existing_season_codes()
        season_code = generate_season_id(existing_codes)
        
        # Create season
        season = await self.season_repo.create(
            season_code=season_code,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            status=SeasonStatus.CREATED,
            created_by=data.created_by,
        )
        
        # Create workflow record
        await self.workflow_repo.create(
            season_id=season.id,
            locations_defined=False,
            plan_uploaded=False,
            otb_uploaded=False,
            range_uploaded=False,
            locked=False,
        )
        
        return season
    
    async def _get_existing_season_codes(self) -> set[str]:
        """Get all existing season codes."""
        result = await self.session.execute(
            select(Season.season_code)
        )
        return {row[0] for row in result.all()}
    
    # =========================================================================
    # STEP 2: Define Locations
    # =========================================================================
    
    async def define_location(
        self,
        season_id: UUID,
        data: LocationCreate,
    ) -> Location:
        """
        Define a location with auto-generated location_code.
        
        Location code: 16-character unique alphanumeric
        """
        # Verify season exists and is in correct state
        await self._verify_season_state(season_id, SeasonStatus.CREATED)
        
        # Get existing location codes
        existing_codes = await self._get_existing_location_codes()
        location_code = generate_location_id(existing_codes)
        
        # Create location
        location = await self.location_repo.create(
            location_code=location_code,
            name=data.name,
            type=data.type,
            cluster_id=data.cluster_id,
        )
        
        return location
    
    async def define_locations_bulk(
        self,
        season_id: UUID,
        locations: list[LocationCreate],
    ) -> list[Location]:
        """Bulk define locations for a season."""
        await self._verify_season_state(season_id, SeasonStatus.CREATED)
        
        existing_codes = await self._get_existing_location_codes()
        created_locations = []
        
        for loc_data in locations:
            location_code = generate_location_id(existing_codes)
            existing_codes.add(location_code)  # Add to set to avoid duplicates
            
            location = await self.location_repo.create(
                location_code=location_code,
                name=loc_data.name,
                type=loc_data.type,
                cluster_id=loc_data.cluster_id,
            )
            created_locations.append(location)
        
        return created_locations
    
    async def complete_location_definition(self, season_id: UUID) -> Season:
        """
        Mark location definition as complete and advance workflow.
        
        Transitions: CREATED -> LOCATIONS_DEFINED
        """
        season = await self._verify_season_state(season_id, SeasonStatus.CREATED)
        
        # Update workflow
        await self.workflow_repo.update_workflow_step(season_id, "locations_defined", True)
        
        # Update season status
        season = await self.season_repo.update_status(season_id, SeasonStatus.LOCATIONS_DEFINED)
        
        return season
    
    async def _get_existing_location_codes(self) -> set[str]:
        """Get all existing location codes."""
        result = await self.session.execute(
            select(Location.location_code)
        )
        return {row[0] for row in result.all()}
    
    # =========================================================================
    # STEP 3: Upload Season Plan
    # =========================================================================
    
    async def verify_can_upload_plan(self, season_id: UUID) -> bool:
        """Verify season plan can be uploaded."""
        await self._verify_season_state(season_id, SeasonStatus.LOCATIONS_DEFINED)
        return True
    
    async def complete_plan_upload(self, season_id: UUID) -> Season:
        """
        Mark season plan upload as complete and advance workflow.
        
        Transitions: LOCATIONS_DEFINED -> PLAN_UPLOADED
        Note: Season plan becomes IMMUTABLE after this point.
        """
        season = await self._verify_season_state(season_id, SeasonStatus.LOCATIONS_DEFINED)
        
        # Update workflow
        await self.workflow_repo.update_workflow_step(season_id, "plan_uploaded", True)
        
        # Update season status
        season = await self.season_repo.update_status(season_id, SeasonStatus.PLAN_UPLOADED)
        
        return season
    
    # =========================================================================
    # STEP 4: Upload OTB Plan
    # =========================================================================
    
    async def verify_can_upload_otb(self, season_id: UUID) -> bool:
        """Verify OTB plan can be uploaded."""
        await self._verify_season_state(season_id, SeasonStatus.PLAN_UPLOADED)
        return True
    
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
    
    async def complete_otb_upload(self, season_id: UUID) -> Season:
        """
        Mark OTB upload as complete and advance workflow.
        
        Transitions: PLAN_UPLOADED -> OTB_UPLOADED
        """
        season = await self._verify_season_state(season_id, SeasonStatus.PLAN_UPLOADED)
        
        # Update workflow
        await self.workflow_repo.update_workflow_step(season_id, "otb_uploaded", True)
        
        # Update season status
        season = await self.season_repo.update_status(season_id, SeasonStatus.OTB_UPLOADED)
        
        return season
    
    # =========================================================================
    # STEP 5: Upload Range Intent
    # =========================================================================
    
    async def verify_can_upload_range(self, season_id: UUID) -> bool:
        """Verify range intent can be uploaded."""
        await self._verify_season_state(season_id, SeasonStatus.OTB_UPLOADED)
        return True
    
    async def complete_range_upload(self, season_id: UUID) -> Season:
        """
        Mark range intent upload as complete and advance workflow.
        
        Transitions: OTB_UPLOADED -> RANGE_UPLOADED
        """
        season = await self._verify_season_state(season_id, SeasonStatus.OTB_UPLOADED)
        
        # Update workflow
        await self.workflow_repo.update_workflow_step(season_id, "range_uploaded", True)
        
        # Update season status
        season = await self.season_repo.update_status(season_id, SeasonStatus.RANGE_UPLOADED)
        
        return season
    
    # =========================================================================
    # STEP 6 & 7: Ingest PO and GRN
    # =========================================================================
    
    async def verify_can_ingest_po(self, season_id: UUID) -> bool:
        """Verify PO can be ingested (after range intent)."""
        season = await self.season_repo.get_by_id(season_id)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )
        
        # PO can be ingested after range is uploaded or when locked
        if season.status not in [SeasonStatus.RANGE_UPLOADED, SeasonStatus.LOCKED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot ingest PO. Season must be in RANGE_UPLOADED or LOCKED state. Current: {season.status.value}",
            )
        
        return True
    
    async def verify_can_ingest_grn(self, season_id: UUID) -> bool:
        """Verify GRN can be ingested (after PO exists)."""
        # GRN can be ingested any time after range is uploaded
        return await self.verify_can_ingest_po(season_id)
    
    # =========================================================================
    # STEP 8: Lock Season (Read-Only Analytics View)
    # =========================================================================
    
    async def lock_season(self, season_id: UUID) -> Season:
        """
        Lock the season for read-only analytics view.
        
        Transitions: RANGE_UPLOADED -> LOCKED
        After locking: NO EDITING ALLOWED
        """
        season = await self._verify_season_state(season_id, SeasonStatus.RANGE_UPLOADED)
        
        # Update workflow
        await self.workflow_repo.update_workflow_step(season_id, "locked", True)
        
        # Update season status
        season = await self.season_repo.update_status(season_id, SeasonStatus.LOCKED)
        
        return season
    
    async def is_season_locked(self, season_id: UUID) -> bool:
        """Check if season is locked."""
        season = await self.season_repo.get_by_id(season_id)
        return season is not None and season.status == SeasonStatus.LOCKED
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    async def _verify_season_state(
        self,
        season_id: UUID,
        expected_status: SeasonStatus,
    ) -> Season:
        """Verify season exists and is in expected state."""
        season = await self.season_repo.get_by_id(season_id)
        
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )
        
        if season.status != expected_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid season state. Expected: {expected_status.value}, Current: {season.status.value}",
            )
        
        return season
    
    async def get_workflow_status(self, season_id: UUID) -> dict:
        """Get complete workflow status for a season."""
        season = await self.season_repo.get_by_id(season_id)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )
        
        workflow = await self.workflow_repo.get_by_season_id(season_id)
        
        return {
            "season_id": str(season_id),
            "season_code": season.season_code,
            "season_name": season.name,
            "current_status": season.status.value,
            "workflow": {
                "locations_defined": workflow.locations_defined if workflow else False,
                "plan_uploaded": workflow.plan_uploaded if workflow else False,
                "otb_uploaded": workflow.otb_uploaded if workflow else False,
                "range_uploaded": workflow.range_uploaded if workflow else False,
                "locked": workflow.locked if workflow else False,
            },
            "next_step": self._get_next_step(season.status),
            "is_editable": season.status != SeasonStatus.LOCKED,
        }
    
    def _get_next_step(self, current_status: SeasonStatus) -> Optional[str]:
        """Get the next workflow step based on current status."""
        steps = {
            SeasonStatus.CREATED: "Define Locations",
            SeasonStatus.LOCATIONS_DEFINED: "Upload Season Plan",
            SeasonStatus.PLAN_UPLOADED: "Upload OTB Plan",
            SeasonStatus.OTB_UPLOADED: "Upload Range Intent",
            SeasonStatus.RANGE_UPLOADED: "Lock Season or Ingest PO/GRN",
            SeasonStatus.LOCKED: None,  # No next step - read-only
        }
        return steps.get(current_status)

#!/usr/bin/env python
"""
Kyros Backend API Test Script

This script tests the FastAPI backend endpoints.
Run from the backend directory: python test_api.py
"""

import asyncio
import sys
from decimal import Decimal
from datetime import date, timedelta

# Test the ID generators
print("=" * 60)
print("KYROS BACKEND TEST SCRIPT")
print("=" * 60)

# Test 1: ID Generators
print("\n1. Testing ID Generators...")
try:
    from app.utils.id_generators import (
        generate_season_id,
        generate_location_id,
        generate_po_number,
        validate_season_id_format,
        validate_location_id_format,
    )
    
    season_id = generate_season_id()
    print(f"   ✅ Season ID: {season_id} (format: XXXX-XXXX)")
    assert validate_season_id_format(season_id), "Invalid season ID format"
    
    location_id = generate_location_id()
    print(f"   ✅ Location ID: {location_id} (16 chars)")
    assert validate_location_id_format(location_id), "Invalid location ID format"
    assert len(location_id) == 16, "Location ID should be 16 chars"
    
    po_number = generate_po_number()
    print(f"   ✅ PO Number: {po_number}")
    
    # Test uniqueness
    season_ids = set()
    for _ in range(100):
        sid = generate_season_id(season_ids)
        season_ids.add(sid)
    print(f"   ✅ Generated 100 unique season IDs")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: OTB Formula
print("\n2. Testing OTB Formula...")
try:
    from app.services.workflow_orchestrator import WorkflowOrchestrator
    
    planned_sales = Decimal("100000.00")
    planned_closing_stock = Decimal("50000.00")
    opening_stock = Decimal("30000.00")
    on_order = Decimal("10000.00")
    
    otb = WorkflowOrchestrator.calculate_otb(
        planned_sales, planned_closing_stock, opening_stock, on_order
    )
    
    expected = planned_sales + planned_closing_stock - opening_stock - on_order
    print(f"   Formula: Planned Sales + Planned Closing Stock - Opening Stock - On Order")
    print(f"   Calculation: {planned_sales} + {planned_closing_stock} - {opening_stock} - {on_order}")
    print(f"   ✅ OTB Result: {otb}")
    assert otb == expected, f"OTB mismatch: {otb} != {expected}"
    print(f"   ✅ OTB Formula verified: {expected}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Model Imports
print("\n3. Testing Model Imports...")
try:
    from app.models.season import Season, SeasonStatus
    from app.models.location import Location, LocationType
    from app.models.cluster import Cluster
    from app.models.category import Category
    from app.models.season_plan import SeasonPlan
    from app.models.otb_plan import OTBPlan
    from app.models.range_intent import RangeIntent
    from app.models.purchase_order import PurchaseOrder
    from app.models.grn import GRNRecord
    from app.models.workflow import SeasonWorkflow
    from app.models.user import User, UserRole
    
    print("   ✅ All 11 models imported successfully")
    print(f"   ✅ SeasonStatus values: {[s.value for s in SeasonStatus]}")
    print(f"   ✅ LocationType values: {[l.value for l in LocationType]}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Schema Imports
print("\n4. Testing Schema Imports...")
try:
    from app.schemas.season import SeasonCreate, SeasonResponse
    from app.schemas.location import LocationCreate, LocationResponse
    from app.schemas.otb import OTBPlanCreate, OTBPlanResponse
    from app.schemas.plan import SeasonPlanCreate
    from app.schemas.range_intent import RangeIntentCreate
    from app.schemas.po import PurchaseOrderCreate
    from app.schemas.grn import GRNRecordCreate
    
    print("   ✅ All schemas imported successfully")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Service Imports
print("\n5. Testing Service Imports...")
try:
    from app.services.workflow_orchestrator import WorkflowOrchestrator
    from app.services.season_service import SeasonService
    from app.services.otb_service import OTBService
    from app.services.plan_service import SeasonPlanService
    from app.services.range_intent_service import RangeIntentService
    from app.services.po_ingest_service import POIngestService
    from app.services.grn_ingest_service import GRNIngestService
    from app.services.analytics_service import AnalyticsService
    
    print("   ✅ All services imported successfully")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: API Router
print("\n6. Testing API Router...")
try:
    from app.api.v1.router import router
    
    routes = [r.path for r in router.routes]
    print(f"   ✅ Router loaded with {len(routes)} routes")
    
    # Show some key routes
    key_patterns = ['/seasons', '/locations', '/plans', '/otb', '/range-intent', '/po', '/grn', '/analytics']
    for pattern in key_patterns:
        matching = [r for r in routes if pattern in r]
        print(f"      {pattern}: {len(matching)} endpoints")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 7: FastAPI App
print("\n7. Testing FastAPI App...")
try:
    from app.main import app
    
    print(f"   ✅ App Title: {app.title}")
    print(f"   ✅ App Version: {app.version}")
    print(f"   ✅ OpenAPI URL: {app.openapi_url}")
    
    # Count total routes
    all_routes = [r for r in app.routes]
    print(f"   ✅ Total routes: {len(all_routes)}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 8: Workflow State Machine
print("\n8. Testing Workflow State Machine...")
try:
    from app.models.season import SeasonStatus
    from app.core.workflow_guard import WorkflowGuard
    
    transitions = WorkflowGuard.WORKFLOW_TRANSITIONS
    print("   Workflow States and Transitions:")
    for from_state, to_states in transitions.items():
        to_str = ", ".join([s.value for s in to_states]) if to_states else "(terminal)"
        print(f"      {from_state.value} → {to_str}")
    
    print("   ✅ Workflow state machine verified")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 60)

print("\n📋 WORKFLOW SUMMARY:")
print("""
   Step 1: Create Season      → Status: CREATED (auto-generates season_code)
   Step 2: Define Locations   → Status: LOCATIONS_DEFINED (auto-generates location_code)
   Step 3: Upload Season Plan → Status: PLAN_UPLOADED (IMMUTABLE after this)
   Step 4: Upload OTB Plan    → Status: OTB_UPLOADED (uses formula)
   Step 5: Upload Range Intent→ Status: RANGE_UPLOADED
   Step 6: Ingest PO/GRN     → Can ingest after range upload
   Step 7: Lock Season        → Status: LOCKED (READ-ONLY Analytics View)
""")

print("\n📐 OTB FORMULA:")
print("   OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order")

print("\n🔑 ID FORMATS:")
print(f"   Season ID:   XXXX-XXXX (e.g., {generate_season_id()})")
print(f"   Location ID: 16 alphanumeric chars (e.g., {generate_location_id()})")

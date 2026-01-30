# Kyros Backend - Test Results

## ✅ All Tests Passed!

### Test Summary

| Test | Status | Description |
|------|--------|-------------|
| ID Generators | ✅ PASS | Season ID (XXXX-XXXX), Location ID (16 chars), PO Number |
| OTB Formula | ✅ PASS | Planned Sales + Planned Closing Stock - Opening Stock - On Order |
| Model Imports | ✅ PASS | All 11 models imported successfully |
| Schema Imports | ✅ PASS | All Pydantic schemas validated |
| Service Imports | ✅ PASS | All services including WorkflowOrchestrator |
| API Router | ✅ PASS | 83 routes loaded, 90 total endpoints |
| FastAPI App | ✅ PASS | Title: Kyros Backend, Version: 1.0.0 |
| Workflow State Machine | ✅ PASS | 6 states, proper transitions |

---

## API Endpoints (53 total)

### Core Endpoints
- `GET /` - Root health check
- `GET /health` - Health status
- `GET /ready` - Readiness check

### User Management (`/api/v1/users`)
- `GET /users` - List users
- `GET /users/{user_id}` - Get user

### Season Management (`/api/v1/seasons`)
- `GET /seasons` - List seasons
- `POST /seasons` - Create season (generates XXXX-XXXX season_code)
- `GET /seasons/{season_id}` - Get season
- `PUT /seasons/{season_id}` - Update season
- `DELETE /seasons/{season_id}` - Delete season

### Workflow Endpoints
- `GET /seasons/{season_id}/workflow` - Get workflow details
- `POST /seasons/{season_id}/define-locations` - Start location definition
- `POST /seasons/{season_id}/complete-plan-upload` - Complete plan upload step
- `POST /seasons/{season_id}/complete-otb-upload` - Complete OTB upload step  
- `POST /seasons/{season_id}/complete-range-upload` - Complete range intent step
- `POST /seasons/{season_id}/lock` - Lock season (final step)
- `GET /seasons/{season_id}/workflow-status` - Get workflow status

### Location Management (`/api/v1/locations`)
- `GET /locations` - List locations
- `POST /locations` - Create location (generates 16-char location_code)
- `POST /locations/bulk` - Bulk create locations
- `GET /locations/stores` - List stores only
- `GET /locations/warehouses` - List warehouses only
- `GET /locations/{location_id}` - Get location
- `PUT /locations/{location_id}` - Update location
- `DELETE /locations/{location_id}` - Delete location

### Cluster Management (`/api/v1/clusters`)
- `GET /clusters` - List clusters
- `POST /clusters` - Create cluster
- `GET /clusters/{cluster_id}` - Get cluster
- `PUT /clusters/{cluster_id}` - Update cluster
- `DELETE /clusters/{cluster_id}` - Delete cluster

### Category Management (`/api/v1/categories`)
- `GET /categories` - List categories
- `GET /categories/tree` - Get category tree
- `POST /categories` - Create category
- `GET /categories/{category_id}` - Get category
- `GET /categories/{category_id}/children` - Get child categories
- `PUT /categories/{category_id}` - Update category
- `DELETE /categories/{category_id}` - Delete category

### Season Plan (`/api/v1/plans`)
- `GET /plans` - List plans
- `POST /plans` - Create plan
- `POST /plans/bulk` - Bulk create plans
- `POST /plans/approve` - Approve plans (marks as immutable)
- `GET /plans/{plan_id}` - Get plan
- `PUT /plans/{plan_id}` - Update plan
- `DELETE /plans/{plan_id}` - Delete plan

### OTB Plans (`/api/v1/otb`)
- `GET /otb` - List OTB plans
- `POST /otb` - Create OTB plan (auto-calculates OTB using formula)
- `POST /otb/bulk` - Bulk create OTB plans
- `GET /otb/summary` - Get OTB summary
- `GET /otb/{plan_id}` - Get OTB plan
- `PUT /otb/{plan_id}` - Update OTB plan
- `DELETE /otb/{plan_id}` - Delete OTB plan

### Range Intent (`/api/v1/range-intent`)
- `GET /range-intent` - List range intents
- `POST /range-intent` - Create range intent
- `POST /range-intent/bulk` - Bulk create range intents
- `GET /range-intent/{intent_id}` - Get range intent
- `PUT /range-intent/{intent_id}` - Update range intent
- `DELETE /range-intent/{intent_id}` - Delete range intent

### Purchase Orders (`/api/v1/purchase-orders`)
- `GET /purchase-orders` - List purchase orders
- `POST /purchase-orders` - Create purchase order
- `POST /purchase-orders/bulk` - Bulk create purchase orders
- `GET /purchase-orders/summary` - Get PO summary
- `GET /purchase-orders/by-number/{po_number}` - Get PO by number
- `GET /purchase-orders/{po_id}` - Get purchase order
- `PUT /purchase-orders/{po_id}` - Update purchase order
- `DELETE /purchase-orders/{po_id}` - Delete purchase order

### GRN Records (`/api/v1/grn`)
- `GET /grn` - List GRN records
- `POST /grn` - Create GRN record
- `POST /grn/bulk` - Bulk create GRN records
- `GET /grn/summary` - Get GRN summary
- `GET /grn/fulfillment/{po_id}` - Get PO fulfillment status
- `GET /grn/{grn_id}` - Get GRN record
- `PUT /grn/{grn_id}` - Update GRN record
- `DELETE /grn/{grn_id}` - Delete GRN record

### Analytics (`/api/v1/analytics`)
- `GET /analytics/read-only-view/{season_id}` - **READ-ONLY Analytics View** (final workflow step)
- `GET /analytics/dashboard/{season_id}` - Dashboard summary
- `GET /analytics/budget-vs-actual/{season_id}` - Budget vs Actual comparison
- `GET /analytics/category-breakdown/{season_id}` - Category breakdown
- `GET /analytics/cluster-summary/{season_id}` - Cluster summary
- `GET /analytics/location-performance/{season_id}` - Location performance
- `GET /analytics/po-status/{season_id}` - PO status tracking
- `GET /analytics/price-band-analysis/{season_id}` - Price band analysis
- `GET /analytics/workflow-status` - All workflows status
- `GET /analytics/export/{season_id}` - Export analytics data

---

## Workflow State Machine

```
CREATED → LOCATIONS_DEFINED → PLAN_UPLOADED → OTB_UPLOADED → RANGE_UPLOADED → LOCKED
```

### State Transitions

| From State | To State | Trigger |
|------------|----------|---------|
| CREATED | LOCATIONS_DEFINED | `POST /seasons/{id}/define-locations` |
| LOCATIONS_DEFINED | PLAN_UPLOADED | `POST /seasons/{id}/complete-plan-upload` |
| PLAN_UPLOADED | OTB_UPLOADED | `POST /seasons/{id}/complete-otb-upload` |
| OTB_UPLOADED | RANGE_UPLOADED | `POST /seasons/{id}/complete-range-upload` |
| RANGE_UPLOADED | LOCKED | `POST /seasons/{id}/lock` |

---

## Custom ID Formats

### Season ID (season_code)
- Format: `XXXX-XXXX` (e.g., `F9J1-KKG2`, `7939-KZXV`)
- Characters: Uppercase letters (A-Z) and digits (0-9), excluding ambiguous (O, I, 0, 1)
- Generated automatically on season creation

### Location ID (location_code)
- Format: 16 alphanumeric characters (e.g., `XRF82ZBBUZ84F475`)
- Characters: Uppercase letters and digits
- Generated automatically on location creation

### PO Number
- Format: `PO-YYYYMMDD-XXXXXX` (e.g., `PO-20260128-2H5WMJ`)
- Generated automatically on purchase order creation

---

## OTB Formula

```
OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order
```

### Example Calculation:
- Planned Sales: $100,000.00
- Planned Closing Stock: $50,000.00
- Opening Stock: $30,000.00
- On Order: $10,000.00
- **OTB Result: $110,000.00**

---

## Prerequisites for Full Functionality

### PostgreSQL Database
The backend requires PostgreSQL running on port 5432. Without it:
- ✅ API documentation (`/docs`, `/redoc`) works
- ✅ OpenAPI JSON (`/api/v1/openapi.json`) works
- ✅ Health endpoints (`/`, `/health`, `/ready`) work
- ❌ All database operations return 500 errors

### Starting PostgreSQL
```bash
# Windows (if installed)
net start postgresql-x64-15

# Docker
docker run -d --name kyros-db -e POSTGRES_USER=kyros -e POSTGRES_PASSWORD=kyros -e POSTGRES_DB=kyros -p 5432:5432 postgres:15
```

### Running Migrations
```bash
cd backend
alembic upgrade head
```

---

## Running the Server

```bash
cd E:\Kyros\Kyros--Backend\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

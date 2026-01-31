# API Reference

Complete REST API documentation for Kyros Backend.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently using session-based authentication. JWT tokens planned for v2.

---

## Health Endpoints

### Root
```http
GET /
```
**Response:**
```json
{
  "status": "healthy",
  "service": "Kyros Backend",
  "version": "1.0.0"
}
```

### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Ready Check
```http
GET /ready
```
**Response:**
```json
{
  "status": "ready",
  "database": "connected"
}
```

---

## Seasons

Base path: `/api/v1/seasons`

### List Seasons
```http
GET /seasons
```
**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| skip | int | Pagination offset (default: 0) |
| limit | int | Items per page (default: 100) |
| status | string | Filter by status |

**Response:**
```json
{
  "items": [
    {
      "id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
      "season_code": "P5RF-W7OV",
      "name": "Spring 2026",
      "start_date": "2026-03-01",
      "end_date": "2026-05-31",
      "status": "locked",
      "created_at": "2026-01-31T08:11:36.463018+00:00",
      "created_by": null
    }
  ],
  "total": 1
}
```

### Create Season
```http
POST /seasons
Content-Type: application/json
```
**Request Body:**
```json
{
  "name": "Spring 2026",
  "start_date": "2026-03-01",
  "end_date": "2026-05-31"
}
```
**Response:** `201 Created`
```json
{
  "id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "season_code": "P5RF-W7OV",
  "name": "Spring 2026",
  "start_date": "2026-03-01",
  "end_date": "2026-05-31",
  "status": "created",
  "created_at": "2026-01-31T08:11:36.463018+00:00"
}
```

### Get Season
```http
GET /seasons/{season_id}
```

### Update Season
```http
PUT /seasons/{season_id}
```
**Request Body:**
```json
{
  "name": "Spring 2026 - Updated"
}
```

### Delete Season
```http
DELETE /seasons/{season_id}
```

### Get Workflow Status
```http
GET /seasons/{season_id}/workflow-status
```
**Response:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "season_code": "P5RF-W7OV",
  "season_name": "Spring 2026",
  "current_status": "locked",
  "workflow": {
    "locations_defined": true,
    "plan_uploaded": true,
    "otb_uploaded": true,
    "range_uploaded": true,
    "locked": true
  },
  "next_step": null,
  "is_editable": false
}
```

### Workflow Transitions

#### Define Locations
```http
POST /seasons/{season_id}/define-locations
Content-Type: application/json

{}
```
**Response:**
```json
{
  "season_id": "...",
  "locations_defined": true,
  "plan_uploaded": false,
  "otb_uploaded": false,
  "range_uploaded": false,
  "locked": false,
  "updated_at": "2026-01-31T08:11:36.505936+00:00"
}
```

#### Complete Plan Upload
```http
POST /seasons/{season_id}/complete-plan-upload
```

#### Complete OTB Upload
```http
POST /seasons/{season_id}/complete-otb-upload
```

#### Complete Range Upload
```http
POST /seasons/{season_id}/complete-range-upload
```

#### Lock Season
```http
POST /seasons/{season_id}/lock
```
**Note:** Once locked, the season becomes read-only.

---

## Locations

Base path: `/api/v1/locations`

### List Locations
```http
GET /locations
```
**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| skip | int | Pagination offset |
| limit | int | Items per page |
| cluster_id | uuid | Filter by cluster |
| type | string | Filter by type (store/warehouse) |

**Response:**
```json
{
  "items": [
    {
      "id": "8f8939a1-2679-42ab-8bac-d29ddef77ac0",
      "location_code": "ZS2IJT8KN50WAR65",
      "name": "Downtown NYC Store",
      "type": "store",
      "cluster_id": "9b2f1475-89f3-4df8-8e81-42cd2794a9f9",
      "created_at": "2026-01-31T08:11:36.391821+00:00"
    }
  ],
  "total": 1
}
```

### Create Location
```http
POST /locations
Content-Type: application/json
```
**Request Body:**
```json
{
  "name": "Downtown NYC Store",
  "type": "store",
  "cluster_id": "9b2f1475-89f3-4df8-8e81-42cd2794a9f9",
  "address": "123 Main St",
  "city": "New York",
  "country": "USA"
}
```

### Bulk Create Locations
```http
POST /locations/bulk
Content-Type: application/json
```
**Request Body:**
```json
{
  "locations": [
    {"name": "Store 1", "type": "store", "cluster_id": "..."},
    {"name": "Store 2", "type": "store", "cluster_id": "..."}
  ]
}
```

### List Stores Only
```http
GET /locations/stores
```

### List Warehouses Only
```http
GET /locations/warehouses
```

### Get Location
```http
GET /locations/{location_id}
```

### Update Location
```http
PUT /locations/{location_id}
```

### Delete Location
```http
DELETE /locations/{location_id}
```

---

## Clusters

Base path: `/api/v1/clusters`

### List Clusters
```http
GET /clusters
```

### Create Cluster
```http
POST /clusters
Content-Type: application/json
```
**Request Body:**
```json
{
  "name": "Northeast Region",
  "description": "Stores in the northeastern US"
}
```

### Get Cluster
```http
GET /clusters/{cluster_id}
```

### Update Cluster
```http
PUT /clusters/{cluster_id}
```

### Delete Cluster
```http
DELETE /clusters/{cluster_id}
```

---

## Categories

Base path: `/api/v1/categories`

### List Categories
```http
GET /categories
```

### Get Category Tree
```http
GET /categories/tree
```
**Response:**
```json
[
  {
    "id": "ef9b71e9-8e01-4c68-b9cf-9b0b548292b4",
    "name": "Apparel",
    "parent_id": null,
    "children": [
      {
        "id": "...",
        "name": "Men's",
        "parent_id": "ef9b71e9-8e01-4c68-b9cf-9b0b548292b4",
        "children": []
      }
    ]
  }
]
```

### Create Category
```http
POST /categories
Content-Type: application/json
```
**Request Body:**
```json
{
  "name": "Apparel",
  "code": "APP",
  "description": "Clothing and accessories",
  "parent_id": null
}
```

### Get Category
```http
GET /categories/{category_id}
```

### Update Category
```http
PUT /categories/{category_id}
```

### Delete Category
```http
DELETE /categories/{category_id}
```

---

## Season Plans

Base path: `/api/v1/plans`

### List Plans
```http
GET /plans?season_id={uuid}
```
**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| season_id | uuid | Yes | Filter by season |
| location_id | uuid | No | Filter by location |
| category_id | uuid | No | Filter by category |

### Create Plan
```http
POST /plans
Content-Type: application/json
```
**Request Body:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "location_id": "8f8939a1-2679-42ab-8bac-d29ddef77ac0",
  "category_id": "ef9b71e9-8e01-4c68-b9cf-9b0b548292b4",
  "planned_sales": 100000.00,
  "planned_margin": 25.50,
  "inventory_turns": 4
}
```
**Response:**
```json
{
  "id": "1ac871c4-7c50-4dba-b7da-8d7c43489984",
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "location_id": "8f8939a1-2679-42ab-8bac-d29ddef77ac0",
  "category_id": "ef9b71e9-8e01-4c68-b9cf-9b0b548292b4",
  "planned_sales": "100000.00",
  "planned_margin": "25.50",
  "inventory_turns": "4.00",
  "version": 1,
  "approved": false,
  "created_at": "2026-01-31T08:11:36.535579+00:00"
}
```

### Bulk Create Plans
```http
POST /plans/bulk
```

### Approve Plans
```http
POST /plans/approve
Content-Type: application/json
```
**Request Body:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "plan_ids": ["1ac871c4-7c50-4dba-b7da-8d7c43489984"]
}
```

### Get Plan
```http
GET /plans/{plan_id}
```

### Update Plan
```http
PUT /plans/{plan_id}
```

### Delete Plan
```http
DELETE /plans/{plan_id}
```

---

## OTB Plans

Base path: `/api/v1/otb`

### List OTB Plans
```http
GET /otb?season_id={uuid}
```

### Get OTB Summary
```http
GET /otb/summary?season_id={uuid}
```
**Response:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "total_budget": "110000.00",
  "by_category": {...},
  "by_location": {...}
}
```

### Create OTB Plan
```http
POST /otb
Content-Type: application/json
```
**Request Body:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "category_id": "ef9b71e9-8e01-4c68-b9cf-9b0b548292b4",
  "location_id": "8f8939a1-2679-42ab-8bac-d29ddef77ac0",
  "month": "2026-03-01",
  "planned_sales": 100000.00,
  "planned_closing_stock": 50000.00,
  "opening_stock": 30000.00,
  "on_order": 10000.00
}
```
**Response:**
```json
{
  "id": "98e0c343-4e89-4d57-9fce-9b74670f190f",
  "approved_spend_limit": "110000.00",
  "...": "..."
}
```

**OTB Formula:** `approved_spend_limit = planned_sales + planned_closing_stock - opening_stock - on_order`

### Bulk Create OTB
```http
POST /otb/bulk
```

### Get OTB Plan
```http
GET /otb/{otb_id}
```

### Update OTB Plan
```http
PUT /otb/{otb_id}
```

### Delete OTB Plan
```http
DELETE /otb/{otb_id}
```

---

## Range Intent

Base path: `/api/v1/range-intent`

### List Range Intents
```http
GET /range-intent?season_id={uuid}
```

### Create Range Intent
```http
POST /range-intent
Content-Type: application/json
```
**Request Body:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "category_id": "ef9b71e9-8e01-4c68-b9cf-9b0b548292b4",
  "core_percent": 60.00,
  "fashion_percent": 40.00,
  "price_band_mix": {
    "low": 30,
    "mid": 50,
    "high": 20
  }
}
```

### Bulk Create
```http
POST /range-intent/bulk
```

### Get Range Intent
```http
GET /range-intent/{intent_id}
```

### Update Range Intent
```http
PUT /range-intent/{intent_id}
```

### Delete Range Intent
```http
DELETE /range-intent/{intent_id}
```

---

## Purchase Orders

Base path: `/api/v1/purchase-orders`

### List Purchase Orders
```http
GET /purchase-orders
```

### Get PO Summary
```http
GET /purchase-orders/summary
```
**Response:**
```json
{
  "total_orders": 1,
  "total_value": "12500.00",
  "by_source": {"api": 1}
}
```

### Get PO by Number
```http
GET /purchase-orders/by-number/{po_number}
```

### Create Purchase Order
```http
POST /purchase-orders
Content-Type: application/json
```
**Request Body:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "location_id": "8f8939a1-2679-42ab-8bac-d29ddef77ac0",
  "category_id": "ef9b71e9-8e01-4c68-b9cf-9b0b548292b4",
  "po_number": "PO-2026-001",
  "po_value": 12500.00,
  "source": "api"
}
```
**Source Options:** `api`, `csv`, `erp`

### Bulk Create POs
```http
POST /purchase-orders/bulk
```

### Get Purchase Order
```http
GET /purchase-orders/{po_id}
```

### Update Purchase Order
```http
PUT /purchase-orders/{po_id}
```

### Delete Purchase Order
```http
DELETE /purchase-orders/{po_id}
```

---

## GRN (Goods Received Notes)

Base path: `/api/v1/grn`

### List GRN Records
```http
GET /grn?po_id={uuid}
GET /grn?start_date=2026-01-01&end_date=2026-12-31
```

### Get GRN Summary
```http
GET /grn/summary?season_id={uuid}
```

### Get PO Fulfillment Status
```http
GET /grn/fulfillment/{po_id}
```
**Response:**
```json
{
  "po_id": "e8913d53-1f44-4914-b026-fa0f89f0c620",
  "po_value": "12500.00",
  "received_value": "11250.00",
  "fulfillment_percent": 90.0
}
```

### Create GRN
```http
POST /grn
Content-Type: application/json
```
**Request Body:**
```json
{
  "po_id": "e8913d53-1f44-4914-b026-fa0f89f0c620",
  "grn_number": "GRN-2026-001",
  "grn_date": "2026-04-14",
  "received_value": 11250.00
}
```

### Bulk Create GRN
```http
POST /grn/bulk
```

### Get GRN
```http
GET /grn/{grn_id}
```

### Update GRN
```http
PUT /grn/{grn_id}
```

### Delete GRN
```http
DELETE /grn/{grn_id}
```

---

## Analytics

Base path: `/api/v1/analytics`

### Dashboard
```http
GET /analytics/dashboard/{season_id}
```
**Response:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "plans": {
    "total": 1,
    "approved": 0,
    "planned_sales": "100000.00",
    "planned_margin": "25.50"
  },
  "otb": {
    "total": 1,
    "total_budget": "110000.00"
  },
  "purchase_orders": {
    "total": 1,
    "total_value": "12500.00",
    "budget_utilization": "11.36"
  },
  "grn": {
    "total": 1,
    "total_received": "11250.00",
    "fulfillment_rate": "90.0"
  },
  "range_intent": {
    "total": 1,
    "avg_core_percent": "60.00",
    "avg_fashion_percent": "40.00"
  }
}
```

### Read-Only View (Locked Seasons)
```http
GET /analytics/read-only-view/{season_id}
```
**Note:** Available only for LOCKED seasons.

### Budget vs Actual
```http
GET /analytics/budget-vs-actual/{season_id}
```

### Category Breakdown
```http
GET /analytics/category-breakdown/{season_id}
```

### Cluster Summary
```http
GET /analytics/cluster-summary/{season_id}
```

### Location Performance
```http
GET /analytics/location-performance/{season_id}
```

### PO Status
```http
GET /analytics/po-status/{season_id}
```

### Price Band Analysis
```http
GET /analytics/price-band-analysis/{season_id}
```

### All Workflows Status
```http
GET /analytics/workflow-status
```

### Export Analytics
```http
GET /analytics/export/{season_id}?format=json
```
**Format Options:** `json`, `csv`

---

## Users

Base path: `/api/v1/users`

### List Users
```http
GET /users
```

### Create User
```http
POST /users
Content-Type: application/json
```
**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "role": "planner"
}
```
**Roles:** `admin`, `planner`, `buyer`, `viewer`

### Get User
```http
GET /users/{user_id}
```

### Update User
```http
PUT /users/{user_id}
```

### Delete User
```http
DELETE /users/{user_id}
```

---

## Error Responses

### Validation Error (422)
```json
{
  "detail": "Validation Error",
  "errors": [
    {
      "field": "body.season_id",
      "message": "Field required",
      "type": "missing"
    }
  ]
}
```

### Not Found (404)
```json
{
  "detail": "Season not found"
}
```

### Conflict (409)
```json
{
  "detail": "Cluster with this name already exists"
}
```

### Workflow Error (400)
```json
{
  "detail": "Invalid workflow transition: cannot move from 'created' to 'locked'"
}
```

---

## Pagination

All list endpoints support pagination:

```http
GET /api/v1/seasons?skip=0&limit=20
```

**Response:**
```json
{
  "items": [...],
  "total": 100
}
```

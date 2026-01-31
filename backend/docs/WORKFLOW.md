# Workflow Guide

Complete guide to the Kyros season planning workflow.

## Overview

Each season follows a strict linear workflow from creation to final lock. Once locked, the season becomes read-only and available for analytics.

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KYROS PLANNING WORKFLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌─────────────────┐    ┌──────────────┐                   │
│  │ CREATED  │───►│LOCATIONS_DEFINED│───►│ PLAN_UPLOADED│                   │
│  └──────────┘    └─────────────────┘    └──────┬───────┘                   │
│       │                  │                      │                          │
│       │ Season           │ Locations            │ Plans                    │
│       │ created          │ assigned             │ uploaded                 │
│       │                  │                      ▼                          │
│       │                  │               ┌──────────────┐                  │
│       │                  │               │ OTB_UPLOADED │                  │
│       │                  │               └──────┬───────┘                  │
│       │                  │                      │                          │
│       │                  │                      │ OTB Budget               │
│       │                  │                      │ calculated               │
│       │                  │                      ▼                          │
│  ┌────┴──────────────────┴──────────────┐ ┌──────────────┐                 │
│  │           IMMUTABLE ZONE             │ │RANGE_UPLOADED│                 │
│  │  (Plans cannot be modified after     │ └──────┬───────┘                 │
│  │   OTB is uploaded)                   │        │                         │
│  └──────────────────────────────────────┘        │ Range Intent            │
│                                                  │ defined                 │
│                                                  ▼                         │
│                            ┌─────────────────────────────────┐             │
│                            │      PO & GRN INGESTION         │             │
│                            │  (Can happen after range upload)│             │
│                            └────────────────┬────────────────┘             │
│                                             │                              │
│                                             ▼                              │
│                                      ┌──────────┐                          │
│                                      │  LOCKED  │                          │
│                                      └──────────┘                          │
│                                             │                              │
│                                             ▼                              │
│                            ┌─────────────────────────────────┐             │
│                            │    READ-ONLY ANALYTICS VIEW     │             │
│                            └─────────────────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## States

### 1. CREATED

Initial state when a new season is created.

**What happens:**
- Season record created
- Unique season code generated (format: XXXX-XXXX)
- Workflow record initialized

**API Call:**
```http
POST /api/v1/seasons
Content-Type: application/json

{
  "name": "Spring 2026",
  "start_date": "2026-03-01",
  "end_date": "2026-05-31"
}
```

**Response:**
```json
{
  "id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "season_code": "P5RF-W7OV",
  "name": "Spring 2026",
  "status": "created"
}
```

**Allowed Actions:**
- ✅ Edit season details
- ✅ Create locations
- ❌ Create plans
- ❌ Create OTB
- ❌ Create range intent

---

### 2. LOCATIONS_DEFINED

Locations have been assigned to the season.

**Transition API:**
```http
POST /api/v1/seasons/{season_id}/define-locations
Content-Type: application/json

{}
```

**Response:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "locations_defined": true,
  "plan_uploaded": false,
  "otb_uploaded": false,
  "range_uploaded": false,
  "locked": false
}
```

**Allowed Actions:**
- ✅ Edit season details
- ✅ Add/remove locations
- ✅ Create plans
- ❌ Create OTB
- ❌ Create range intent

---

### 3. PLAN_UPLOADED

Season plans have been uploaded.

**Before Transition:**
Create plans for the season:
```http
POST /api/v1/plans
Content-Type: application/json

{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "location_id": "8f8939a1-2679-42ab-8bac-d29ddef77ac0",
  "category_id": "ef9b71e9-8e01-4c68-b9cf-9b0b548292b4",
  "planned_sales": 100000.00,
  "planned_margin": 25.50,
  "inventory_turns": 4
}
```

**Transition API:**
```http
POST /api/v1/seasons/{season_id}/complete-plan-upload
```

**Allowed Actions:**
- ⚠️ Edit season details (limited)
- ✅ View plans
- ✅ Create OTB
- ❌ Create range intent
- ❌ Modify plans (becoming immutable)

---

### 4. OTB_UPLOADED

Open-To-Buy budget has been calculated and uploaded.

**Before Transition:**
Create OTB plans:
```http
POST /api/v1/otb
Content-Type: application/json

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

**OTB Formula:**
```
OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order
    = 100,000 + 50,000 - 30,000 - 10,000
    = 110,000
```

**Transition API:**
```http
POST /api/v1/seasons/{season_id}/complete-otb-upload
```

**Allowed Actions:**
- ❌ Modify plans (IMMUTABLE)
- ✅ View OTB
- ✅ Create range intent
- ❌ Modify OTB

---

### 5. RANGE_UPLOADED

Range intent has been defined.

**Before Transition:**
Create range intents:
```http
POST /api/v1/range-intent
Content-Type: application/json

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

**Transition API:**
```http
POST /api/v1/seasons/{season_id}/complete-range-upload
```

**Allowed Actions:**
- ✅ Create Purchase Orders
- ✅ Create GRN records
- ✅ View all data
- ❌ Modify plans, OTB, range intent

---

### 6. LOCKED

Final state - season is complete and read-only.

**Before Transition (Optional):**
Create purchase orders and GRN:
```http
POST /api/v1/purchase-orders
{
  "season_id": "...",
  "location_id": "...",
  "category_id": "...",
  "po_number": "PO-2026-001",
  "po_value": 12500.00,
  "source": "api"
}

POST /api/v1/grn
{
  "po_id": "...",
  "grn_number": "GRN-2026-001",
  "grn_date": "2026-04-14",
  "received_value": 11250.00
}
```

**Transition API:**
```http
POST /api/v1/seasons/{season_id}/lock
```

**Response:**
```json
{
  "season_id": "6cb6fb4a-50cc-433c-a3f2-c85b2c7acb49",
  "locations_defined": true,
  "plan_uploaded": true,
  "otb_uploaded": true,
  "range_uploaded": true,
  "locked": true
}
```

**Allowed Actions:**
- ✅ View all data (read-only)
- ✅ Access analytics dashboard
- ✅ Export reports
- ❌ ANY modifications

---

## Checking Workflow Status

```http
GET /api/v1/seasons/{season_id}/workflow-status
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

---

## Workflow Transitions Summary

| From | To | Endpoint |
|------|----|----------|
| created | locations_defined | `POST /seasons/{id}/define-locations` |
| locations_defined | plan_uploaded | `POST /seasons/{id}/complete-plan-upload` |
| plan_uploaded | otb_uploaded | `POST /seasons/{id}/complete-otb-upload` |
| otb_uploaded | range_uploaded | `POST /seasons/{id}/complete-range-upload` |
| range_uploaded | locked | `POST /seasons/{id}/lock` |

---

## Error Handling

### Invalid Transition
```http
POST /api/v1/seasons/{season_id}/lock
```
When season is not in `range_uploaded` status:

```json
{
  "detail": "Invalid workflow transition: cannot move from 'created' to 'locked'"
}
```

### Modifying Locked Season
```http
PUT /api/v1/plans/{plan_id}
```
When season is locked:

```json
{
  "detail": "Season is locked and cannot be modified"
}
```

---

## Analytics Access

After locking, access the read-only analytics view:

```http
GET /api/v1/analytics/read-only-view/{season_id}
```

**Full Dashboard:**
```http
GET /api/v1/analytics/dashboard/{season_id}
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

---

## Best Practices

1. **Complete each step before transitioning** - Ensure all data is uploaded before moving to the next state

2. **Validate data quality** - Review plans and OTB before marking complete

3. **Use bulk operations** - Use `/bulk` endpoints for large data uploads

4. **Monitor workflow status** - Regularly check workflow status during the planning cycle

5. **Export before locking** - Generate reports before final lock if needed

6. **Plan PO timing** - Create purchase orders before locking to ensure they're tracked

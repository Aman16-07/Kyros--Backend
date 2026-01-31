# Database Schema

Complete database schema documentation for Kyros Backend.

## Overview

The database consists of 11 core entities with PostgreSQL as the primary database.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE SCHEMA                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐                         │
│   │  Users   │      │ Clusters │◄─────│Locations │                         │
│   └────┬─────┘      └──────────┘      └────┬─────┘                         │
│        │                                    │                               │
│        │ created_by                         │ location_id                   │
│        ▼                                    ▼                               │
│   ┌──────────┐      ┌────────────┐    ┌──────────┐                         │
│   │ Seasons  │◄─────│  Workflow  │    │Categories│                         │
│   └────┬─────┘      └────────────┘    └────┬─────┘                         │
│        │                                    │                               │
│        │ season_id                          │ category_id                   │
│        ▼                                    ▼                               │
│   ┌──────────┐    ┌──────────┐    ┌─────────────┐                          │
│   │  Plans   │    │   OTB    │    │Range Intent │                          │
│   └──────────┘    └──────────┘    └─────────────┘                          │
│                                                                              │
│   ┌─────────────────┐      ┌──────────┐                                    │
│   │ Purchase Orders │◄─────│   GRN    │                                    │
│   └─────────────────┘      └──────────┘                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tables

### users

Stores user accounts and authentication data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| full_name | VARCHAR(255) | | User's display name |
| role | ENUM | NOT NULL | admin, planner, buyer, viewer |
| is_active | BOOLEAN | DEFAULT true | Account status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Indexes:**
- `ix_users_email` on email (unique)

**Relationships:**
- One-to-Many → seasons (created_by)
- One-to-Many → season_plans (uploaded_by)

---

### seasons

Represents business planning periods.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| season_code | VARCHAR(9) | UNIQUE, NOT NULL | Custom ID format: XXXX-XXXX |
| name | VARCHAR(255) | NOT NULL | Season name (e.g., "Spring 2026") |
| start_date | DATE | NOT NULL | Season start date |
| end_date | DATE | NOT NULL | Season end date |
| status | ENUM | NOT NULL | Workflow status |
| created_by | UUID | FK → users.id | Creator reference |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Status Values:**
- `created` - Initial state
- `locations_defined` - Locations assigned
- `plan_uploaded` - Plans uploaded
- `otb_uploaded` - OTB budget set
- `range_uploaded` - Range intent defined
- `locked` - Read-only (final)

**Indexes:**
- `ix_seasons_season_code` on season_code (unique)
- `ix_seasons_status` on status

**Relationships:**
- Many-to-One → users (created_by)
- One-to-One → season_workflows
- One-to-Many → season_plans
- One-to-Many → otb_plan
- One-to-Many → range_intents
- One-to-Many → purchase_orders

---

### season_workflows

Tracks workflow state for each season.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| season_id | UUID | FK, UNIQUE | Reference to season |
| locations_defined | BOOLEAN | DEFAULT false | Step 1 complete |
| plan_uploaded | BOOLEAN | DEFAULT false | Step 2 complete |
| otb_uploaded | BOOLEAN | DEFAULT false | Step 3 complete |
| range_uploaded | BOOLEAN | DEFAULT false | Step 4 complete |
| locked | BOOLEAN | DEFAULT false | Final step complete |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Relationships:**
- One-to-One → seasons (season_id)

---

### clusters

Groups of locations by region/category.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(255) | UNIQUE, NOT NULL | Cluster name |
| description | TEXT | | Optional description |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Indexes:**
- `ix_clusters_name` on name (unique)

**Relationships:**
- One-to-Many → locations

---

### locations

Stores and warehouses.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| location_code | VARCHAR(16) | UNIQUE, NOT NULL | 16-character alphanumeric code |
| name | VARCHAR(255) | NOT NULL | Location name |
| type | ENUM | NOT NULL | store, warehouse |
| cluster_id | UUID | FK → clusters.id | Parent cluster |
| address | VARCHAR(500) | | Street address |
| city | VARCHAR(100) | | City |
| country | VARCHAR(100) | | Country |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Indexes:**
- `ix_locations_location_code` on location_code (unique)
- `ix_locations_cluster_id` on cluster_id
- `ix_locations_type` on type

**Relationships:**
- Many-to-One → clusters (cluster_id)
- One-to-Many → season_plans
- One-to-Many → otb_plan
- One-to-Many → purchase_orders

---

### categories

Product category hierarchy.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Category name |
| code | VARCHAR(50) | | Short code (e.g., "APP") |
| description | TEXT | | Optional description |
| parent_id | UUID | FK → categories.id | Parent category (self-referential) |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Indexes:**
- `ix_categories_parent_id` on parent_id

**Relationships:**
- Self-referential Many-to-One → categories (parent_id)
- One-to-Many → season_plans
- One-to-Many → otb_plan
- One-to-Many → range_intents
- One-to-Many → purchase_orders

---

### season_plans

Sales and margin targets by location/category.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| season_id | UUID | FK, NOT NULL | Reference to season |
| location_id | UUID | FK, NOT NULL | Reference to location |
| category_id | UUID | FK, NOT NULL | Reference to category |
| planned_sales | NUMERIC(18,2) | NOT NULL | Target sales value |
| planned_margin | NUMERIC(5,2) | NOT NULL | Target margin percentage |
| inventory_turns | NUMERIC(5,2) | | Target inventory turns |
| version | INTEGER | DEFAULT 1 | Version number |
| approved | BOOLEAN | DEFAULT false | Approval status |
| uploaded_by | UUID | FK → users.id | Uploader reference |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Constraints:**
- `uq_season_plan_composite` UNIQUE (season_id, location_id, category_id)

**Indexes:**
- `ix_season_plans_season_id` on season_id
- `ix_season_plans_location_id` on location_id

**Relationships:**
- Many-to-One → seasons (season_id)
- Many-to-One → locations (location_id)
- Many-to-One → categories (category_id)
- Many-to-One → users (uploaded_by)

---

### otb_plan

Open-To-Buy budget allocation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| season_id | UUID | FK, NOT NULL | Reference to season |
| location_id | UUID | FK, NOT NULL | Reference to location |
| category_id | UUID | FK, NOT NULL | Reference to category |
| month | DATE | NOT NULL | Budget month |
| planned_sales | NUMERIC(18,2) | DEFAULT 0 | Planned sales |
| planned_closing_stock | NUMERIC(18,2) | DEFAULT 0 | Target closing inventory |
| opening_stock | NUMERIC(18,2) | DEFAULT 0 | Beginning inventory |
| on_order | NUMERIC(18,2) | DEFAULT 0 | Pending orders |
| approved_spend_limit | NUMERIC(18,2) | NOT NULL | Calculated OTB |
| uploaded_by | UUID | FK → users.id | Uploader reference |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**OTB Formula:**
```
approved_spend_limit = planned_sales + planned_closing_stock - opening_stock - on_order
```

**Constraints:**
- `uq_otb_plan_composite` UNIQUE (season_id, location_id, category_id, month)

**Indexes:**
- `ix_otb_plan_season_id` on season_id
- `ix_otb_plan_month` on month

**Relationships:**
- Many-to-One → seasons (season_id)
- Many-to-One → locations (location_id)
- Many-to-One → categories (category_id)
- Many-to-One → users (uploaded_by)

---

### range_intents

Product assortment planning.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| season_id | UUID | FK, NOT NULL | Reference to season |
| category_id | UUID | FK, NOT NULL | Reference to category |
| core_percent | NUMERIC(5,2) | NOT NULL | Core product percentage |
| fashion_percent | NUMERIC(5,2) | NOT NULL | Fashion product percentage |
| price_band_mix | JSON | | Price tier distribution |
| uploaded_by | UUID | FK → users.id | Uploader reference |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**price_band_mix Example:**
```json
{
  "low": 30,
  "mid": 50,
  "high": 20
}
```

**Constraints:**
- `core_percent + fashion_percent = 100` (validated at application level)

**Indexes:**
- `ix_range_intents_season_id` on season_id

**Relationships:**
- Many-to-One → seasons (season_id)
- Many-to-One → categories (category_id)
- Many-to-One → users (uploaded_by)

---

### purchase_orders

Procurement orders.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| po_number | VARCHAR(50) | UNIQUE, NOT NULL | Purchase order number |
| season_id | UUID | FK, NOT NULL | Reference to season |
| location_id | UUID | FK, NOT NULL | Destination location |
| category_id | UUID | FK, NOT NULL | Product category |
| po_value | NUMERIC(18,2) | NOT NULL | Order total value |
| source | ENUM | NOT NULL | api, csv, erp |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Indexes:**
- `ix_purchase_orders_po_number` on po_number (unique)
- `ix_purchase_orders_season_id` on season_id
- `ix_purchase_orders_source` on source

**Relationships:**
- Many-to-One → seasons (season_id)
- Many-to-One → locations (location_id)
- Many-to-One → categories (category_id)
- One-to-Many → grn_records

---

### grn_records

Goods Received Notes - tracks actual deliveries.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| po_id | UUID | FK, NOT NULL | Reference to purchase order |
| grn_number | VARCHAR(50) | UNIQUE | GRN document number |
| grn_date | DATE | NOT NULL | Receipt date |
| received_value | NUMERIC(18,2) | NOT NULL | Value of goods received |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | | Last update timestamp |

**Indexes:**
- `ix_grn_records_po_id` on po_id
- `ix_grn_records_grn_date` on grn_date

**Relationships:**
- Many-to-One → purchase_orders (po_id)

---

## Enumerations

### UserRole
```sql
CREATE TYPE user_role AS ENUM ('admin', 'planner', 'buyer', 'viewer');
```

### SeasonStatus
```sql
CREATE TYPE season_status AS ENUM (
  'created',
  'locations_defined',
  'plan_uploaded',
  'otb_uploaded',
  'range_uploaded',
  'locked'
);
```

### LocationType
```sql
CREATE TYPE location_type AS ENUM ('store', 'warehouse');
```

### POSource
```sql
CREATE TYPE po_source AS ENUM ('api', 'csv', 'erp');
```

---

## Custom ID Generation

### Season Code (XXXX-XXXX)
```python
def generate_season_id() -> str:
    """Generate 8-character season code: XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(chars, k=4))
    part2 = ''.join(random.choices(chars, k=4))
    return f"{part1}-{part2}"
    
# Example: P5RF-W7OV, E8AA-X78V
```

### Location Code (16 characters)
```python
def generate_location_id() -> str:
    """Generate 16-character alphanumeric location code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=16))
    
# Example: ZS2IJT8KN50WAR65, MMK5VMGLFCA8E18S
```

---

## Indexes Summary

| Table | Index Name | Columns | Type |
|-------|------------|---------|------|
| users | ix_users_email | email | UNIQUE |
| seasons | ix_seasons_season_code | season_code | UNIQUE |
| seasons | ix_seasons_status | status | |
| clusters | ix_clusters_name | name | UNIQUE |
| locations | ix_locations_location_code | location_code | UNIQUE |
| locations | ix_locations_cluster_id | cluster_id | |
| locations | ix_locations_type | type | |
| categories | ix_categories_parent_id | parent_id | |
| season_plans | ix_season_plans_season_id | season_id | |
| otb_plan | ix_otb_plan_season_id | season_id | |
| purchase_orders | ix_purchase_orders_po_number | po_number | UNIQUE |
| grn_records | ix_grn_records_po_id | po_id | |
| grn_records | ix_grn_records_grn_date | grn_date | |

---

## Migration Commands

Using Alembic for database migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1

# View current version
alembic current

# View history
alembic history
```

---

## Database Connection

PostgreSQL connection string format:

```
postgresql+asyncpg://kyros:kyros@localhost:5432/kyros
```

Components:
- **Driver:** asyncpg (async PostgreSQL)
- **User:** kyros
- **Password:** kyros
- **Host:** localhost (or `db` in Docker)
- **Port:** 5432
- **Database:** kyros

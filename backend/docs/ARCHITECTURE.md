# Architecture

Complete architecture documentation for Kyros Backend.

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Framework | FastAPI | 0.109+ |
| Language | Python | 3.11+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | PostgreSQL | 15 |
| DB Driver | asyncpg | 0.29+ |
| Validation | Pydantic | 2.5+ |
| Migrations | Alembic | 1.13+ |
| Container | Docker | 24+ |
| Server | Uvicorn | 0.27+ |

---

## Directory Structure

```
backend/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   │
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   └── v1/                   # Version 1 endpoints
│   │       ├── __init__.py
│   │       ├── router.py         # Route aggregation
│   │       ├── analytics.py      # Analytics endpoints
│   │       ├── categories.py     # Category CRUD
│   │       ├── clusters.py       # Cluster CRUD
│   │       ├── grn.py            # GRN endpoints
│   │       ├── locations.py      # Location CRUD
│   │       ├── otb.py            # OTB endpoints
│   │       ├── plans.py          # Season plan endpoints
│   │       ├── po.py             # Purchase order endpoints
│   │       ├── range_intent.py   # Range intent endpoints
│   │       ├── seasons.py        # Season + workflow endpoints
│   │       └── users.py          # User management
│   │
│   ├── core/                     # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py             # Settings management
│   │   ├── database.py           # Database connection
│   │   ├── deps.py               # Dependency injection
│   │   ├── security.py           # Authentication/authorization
│   │   └── workflow_guard.py     # Workflow state validation
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── __init__.py           # Model exports
│   │   ├── base.py               # Base model classes
│   │   ├── category.py           # Category model
│   │   ├── cluster.py            # Cluster model
│   │   ├── grn.py                # GRN model
│   │   ├── location.py           # Location model
│   │   ├── otb_plan.py           # OTB model
│   │   ├── purchase_order.py     # PO model
│   │   ├── range_intent.py       # Range intent model
│   │   ├── season.py             # Season model
│   │   ├── season_plan.py        # Season plan model
│   │   ├── user.py               # User model
│   │   └── workflow.py           # Workflow model
│   │
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py           # Schema exports
│   │   ├── base.py               # Base schemas
│   │   ├── category.py           # Category schemas
│   │   ├── cluster.py            # Cluster schemas
│   │   ├── grn.py                # GRN schemas
│   │   ├── location.py           # Location schemas
│   │   ├── otb.py                # OTB schemas
│   │   ├── plan.py               # Plan schemas
│   │   ├── po.py                 # PO schemas
│   │   ├── range_intent.py       # Range intent schemas
│   │   ├── season.py             # Season schemas
│   │   └── user.py               # User schemas
│   │
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   ├── base_repo.py          # Base repository class
│   │   ├── category_repo.py      # Category repository
│   │   ├── cluster_repo.py       # Cluster repository
│   │   ├── grn_repo.py           # GRN repository
│   │   ├── location_repo.py      # Location repository
│   │   ├── otb_repo.py           # OTB repository
│   │   ├── plan_repo.py          # Plan repository
│   │   ├── po_repo.py            # PO repository
│   │   ├── range_intent_repo.py  # Range intent repository
│   │   ├── season_repo.py        # Season repository
│   │   └── user_repo.py          # User repository
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── analytics_service.py       # Analytics calculations
│   │   ├── grn_ingest_service.py      # GRN import logic
│   │   ├── otb_service.py             # OTB calculations
│   │   ├── plan_service.py            # Plan operations
│   │   ├── po_ingest_service.py       # PO import logic
│   │   ├── range_intent_service.py    # Range calculations
│   │   ├── season_service.py          # Season operations
│   │   └── workflow_orchestrator.py   # Workflow state machine
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── csv_loader.py         # CSV import utilities
│   │   ├── id_generators.py      # Custom ID generation
│   │   └── validators.py         # Custom validators
│   │
│   └── tests/                    # Test package
│       └── __init__.py
│
├── alembic/                      # Database migrations
│   ├── env.py                    # Migration environment
│   └── versions/                 # Migration scripts
│
├── docs/                         # Documentation
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── FRONTEND_INTEGRATION.md
│   └── WORKFLOW.md
│
├── .env                          # Environment variables
├── alembic.ini                   # Alembic configuration
├── docker-compose.yml            # Container orchestration
├── Dockerfile                    # Backend container
├── requirements.txt              # Python dependencies
├── test_api.py                   # Test script
├── curl_tests.sh                 # Bash test script
├── curl_tests.ps1                # PowerShell test script
└── README.md                     # Project readme
```

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (Frontend)                               │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ HTTP/JSON
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER (FastAPI)                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  app/api/v1/                                                          │  │
│  │  ├── router.py          # Aggregates all routers                      │  │
│  │  ├── seasons.py         # 12 endpoints                                │  │
│  │  ├── locations.py       # 8 endpoints                                 │  │
│  │  ├── clusters.py        # 5 endpoints                                 │  │
│  │  ├── categories.py      # 6 endpoints                                 │  │
│  │  ├── plans.py           # 7 endpoints                                 │  │
│  │  ├── otb.py             # 7 endpoints                                 │  │
│  │  ├── range_intent.py    # 6 endpoints                                 │  │
│  │  ├── po.py              # 8 endpoints                                 │  │
│  │  ├── grn.py             # 8 endpoints                                 │  │
│  │  ├── analytics.py       # 10 endpoints                                │  │
│  │  └── users.py           # 5 endpoints                                 │  │
│  │                                                                       │  │
│  │  Total: 90 endpoints                                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  app/services/                                                        │  │
│  │  ├── workflow_orchestrator.py   # State machine logic                 │  │
│  │  ├── plan_service.py            # Plan business logic                 │  │
│  │  ├── otb_service.py             # OTB formula calculations            │  │
│  │  ├── analytics_service.py       # Reporting calculations              │  │
│  │  ├── po_ingest_service.py       # PO import processing                │  │
│  │  └── grn_ingest_service.py      # GRN import processing               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REPOSITORY LAYER                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  app/repositories/                                                    │  │
│  │  ├── base_repo.py       # Generic CRUD operations                     │  │
│  │  ├── season_repo.py     # Season-specific queries                     │  │
│  │  ├── location_repo.py   # Location queries                            │  │
│  │  ├── plan_repo.py       # Plan queries                                │  │
│  │  ├── otb_repo.py        # OTB queries                                 │  │
│  │  └── ...                # Other repositories                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MODEL LAYER (SQLAlchemy)                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  app/models/                                                          │  │
│  │  ├── base.py            # Base, TimestampMixin, UUIDPrimaryKeyMixin   │  │
│  │  ├── season.py          # Season + SeasonStatus enum                  │  │
│  │  ├── location.py        # Location + LocationType enum                │  │
│  │  ├── otb_plan.py        # OTB with formula property                   │  │
│  │  └── ...                # 11 total models                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATABASE (PostgreSQL)                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Tables:                                                              │  │
│  │  users, seasons, season_workflows, clusters, locations, categories,  │  │
│  │  season_plans, otb_plan, range_intents, purchase_orders, grn_records │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. main.py - Application Entry Point

```python
# Key responsibilities:
# - FastAPI app initialization
# - Lifespan management (startup/shutdown)
# - Router inclusion
# - CORS configuration
# - Exception handlers

from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Close connections
    await async_engine.dispose()

app = FastAPI(
    title="Kyros Backend",
    version="1.0.0",
    lifespan=lifespan
)
```

### 2. Base Model

```python
# app/models/base.py

class UUIDPrimaryKeyMixin:
    """Provides UUID primary key."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

class TimestampMixin:
    """Provides created_at and updated_at."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )
```

### 3. Repository Pattern

```python
# app/repositories/base_repo.py

class BaseRepository(Generic[ModelType]):
    """Base repository with CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get(self, id: UUID) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100):
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
```

### 4. Dependency Injection

```python
# app/core/deps.py

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# Usage in endpoints:
@router.get("/seasons")
async def list_seasons(db: AsyncSession = Depends(get_db)):
    repo = SeasonRepository(db)
    return await repo.get_all()
```

### 5. ID Generators

```python
# app/utils/id_generators.py

def generate_season_id() -> str:
    """Generate season code: XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(chars, k=4))
    part2 = ''.join(random.choices(chars, k=4))
    return f"{part1}-{part2}"

def generate_location_id() -> str:
    """Generate 16-char location code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=16))
```

### 6. Workflow Orchestrator

```python
# app/services/workflow_orchestrator.py

class WorkflowOrchestrator:
    """Manages season workflow state transitions."""
    
    TRANSITIONS = {
        SeasonStatus.CREATED: SeasonStatus.LOCATIONS_DEFINED,
        SeasonStatus.LOCATIONS_DEFINED: SeasonStatus.PLAN_UPLOADED,
        SeasonStatus.PLAN_UPLOADED: SeasonStatus.OTB_UPLOADED,
        SeasonStatus.OTB_UPLOADED: SeasonStatus.RANGE_UPLOADED,
        SeasonStatus.RANGE_UPLOADED: SeasonStatus.LOCKED,
    }
    
    async def transition(self, season_id: UUID, target_status: SeasonStatus):
        season = await self.get_season(season_id)
        expected = self.TRANSITIONS.get(season.status)
        
        if expected != target_status:
            raise WorkflowError(
                f"Invalid transition: {season.status} → {target_status}"
            )
        
        season.status = target_status
        await self.db.commit()
```

---

## Data Flow

### Create Season Flow

```
1. POST /api/v1/seasons
   │
   ▼
2. seasons.py (API endpoint)
   │  - Validate request with Pydantic schema
   │  - Call service layer
   │
   ▼
3. season_service.py
   │  - Generate season_code using id_generators
   │  - Create Season model
   │  - Create SeasonWorkflow model
   │
   ▼
4. season_repo.py
   │  - Insert into database
   │  - Commit transaction
   │
   ▼
5. Return SeasonResponse
```

### OTB Calculation Flow

```
1. POST /api/v1/otb
   │
   ▼
2. Request Body:
   {
     "planned_sales": 100000,
     "planned_closing_stock": 50000,
     "opening_stock": 30000,
     "on_order": 10000
   }
   │
   ▼
3. otb_service.py - calculate_otb()
   │  OTB = 100000 + 50000 - 30000 - 10000 = 110000
   │
   ▼
4. Store approved_spend_limit = 110000
```

---

## Configuration

### Environment Variables

```python
# app/core/config.py

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://kyros:kyros@localhost:5432/kyros"
    
    # Security
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
```

### Docker Configuration

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: kyros
      POSTGRES_PASSWORD: kyros
      POSTGRES_DB: kyros
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kyros"]
      
  backend:
    build: .
    environment:
      DATABASE_URL: postgresql+asyncpg://kyros:kyros@db:5432/kyros
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
```

---

## Error Handling

### Exception Handlers

```python
# app/main.py

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "errors": [
                {
                    "field": ".".join(str(x) for x in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"]
                }
                for err in exc.errors()
            ]
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )
```

---

## Testing

### Test Structure

```python
# test_api.py

def test_id_generators():
    """Test custom ID generation."""
    season_id = generate_season_id()
    assert len(season_id) == 9  # XXXX-XXXX
    assert season_id[4] == '-'

def test_otb_formula():
    """Test OTB calculation."""
    result = calculate_otb(
        planned_sales=100000,
        planned_closing_stock=50000,
        opening_stock=30000,
        on_order=10000
    )
    assert result == 110000

def test_workflow_transitions():
    """Test valid workflow transitions."""
    assert TRANSITIONS[SeasonStatus.CREATED] == SeasonStatus.LOCATIONS_DEFINED
```

---

## Performance Considerations

1. **Async Database Operations** - All DB calls use async/await
2. **Connection Pooling** - SQLAlchemy async engine manages pool
3. **Pagination** - All list endpoints support skip/limit
4. **Indexes** - Key columns indexed for fast lookups
5. **Eager Loading** - Relationships loaded as needed

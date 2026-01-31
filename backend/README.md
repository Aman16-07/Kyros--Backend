# Kyros Backend

A comprehensive FastAPI backend for retail merchandise planning and workflow management. Built with Python, SQLAlchemy 2.0, PostgreSQL, and Docker.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git

### Option 1: Docker (Recommended)

```bash
# Clone and navigate
cd Kyros--Backend/backend

# Build and start all containers
docker-compose up --build -d

# Check status
docker ps

# API is available at http://localhost:8000
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (Docker)
docker run -d --name kyros-db \
  -e POSTGRES_USER=kyros \
  -e POSTGRES_PASSWORD=kyros \
  -e POSTGRES_DB=kyros \
  -p 5432:5432 postgres:15

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# API Documentation
open http://localhost:8000/docs
```

## 📚 Documentation

Detailed documentation is available in the `/docs` folder:

| Document | Description |
|----------|-------------|
| [API Reference](docs/API_REFERENCE.md) | Complete REST API endpoints |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Models, tables, and relationships |
| [Workflow Guide](docs/WORKFLOW.md) | Season planning workflow states |
| [Architecture](docs/ARCHITECTURE.md) | Project structure and patterns |
| [Frontend Integration](docs/FRONTEND_INTEGRATION.md) | Guide for frontend developers |

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI App                          │
├─────────────────────────────────────────────────────────────┤
│  API Layer (app/api/v1/)                                    │
│  ├── seasons.py, locations.py, clusters.py, categories.py  │
│  ├── plans.py, otb.py, range_intent.py                      │
│  ├── po.py, grn.py, analytics.py, users.py                  │
├─────────────────────────────────────────────────────────────┤
│  Service Layer (app/services/)                              │
│  ├── workflow_orchestrator.py - State machine management    │
│  ├── plan_service.py, otb_service.py                        │
│  ├── po_ingest_service.py, grn_ingest_service.py           │
├─────────────────────────────────────────────────────────────┤
│  Repository Layer (app/repositories/)                       │
│  ├── Base CRUD operations                                   │
│  ├── Entity-specific queries                                │
├─────────────────────────────────────────────────────────────┤
│  Model Layer (app/models/)                                  │
│  ├── SQLAlchemy 2.0 ORM models                              │
│  ├── 11 core entities + relationships                       │
├─────────────────────────────────────────────────────────────┤
│  Database: PostgreSQL 15 (asyncpg driver)                   │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Core Entities

| Entity | Description | Custom ID Format |
|--------|-------------|------------------|
| Season | Planning period (Spring 2026) | `XXXX-XXXX` (e.g., P5RF-W7OV) |
| Location | Store or warehouse | 16 alphanumeric (e.g., ZS2IJT8KN50WAR65) |
| Cluster | Group of locations | UUID |
| Category | Product hierarchy | UUID |
| SeasonPlan | Sales/margin targets | UUID |
| OTBPlan | Open-To-Buy budget | UUID |
| RangeIntent | Core/fashion mix | UUID |
| PurchaseOrder | Procurement orders | UUID + PO Number |
| GRN | Goods received | UUID |

## 🔄 Workflow States

```
CREATED → LOCATIONS_DEFINED → PLAN_UPLOADED → OTB_UPLOADED → RANGE_UPLOADED → LOCKED
```

Each season progresses through these states. Once LOCKED, the season becomes read-only.

## 📐 OTB Formula

```
OTB = Planned Sales + Planned Closing Stock - Opening Stock - On Order
```

Example: `110,000 = 100,000 + 50,000 - 30,000 - 10,000`

## 🔌 API Endpoints Summary

| Resource | Endpoints | Base Path |
|----------|-----------|-----------|
| Seasons | 12 | `/api/v1/seasons` |
| Locations | 8 | `/api/v1/locations` |
| Clusters | 5 | `/api/v1/clusters` |
| Categories | 6 | `/api/v1/categories` |
| Plans | 7 | `/api/v1/plans` |
| OTB | 7 | `/api/v1/otb` |
| Range Intent | 6 | `/api/v1/range-intent` |
| Purchase Orders | 8 | `/api/v1/purchase-orders` |
| GRN | 8 | `/api/v1/grn` |
| Analytics | 10 | `/api/v1/analytics` |
| **Total** | **90** | |

## 🧪 Testing

```bash
# Run Python tests
python test_api.py

# Run curl tests (Linux/WSL)
chmod +x curl_tests.sh
./curl_tests.sh

# Run PowerShell tests (Windows)
.\curl_tests.ps1
```

## 🐳 Docker Commands

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up --build -d

# Access database
docker exec -it kyros-db psql -U kyros -d kyros
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── api/v1/              # API endpoints (11 routers)
│   ├── core/                # Config, database, security
│   ├── models/              # SQLAlchemy models (11 entities)
│   ├── schemas/             # Pydantic schemas
│   ├── repositories/        # Database access layer
│   ├── services/            # Business logic
│   └── utils/               # ID generators, validators
├── alembic/                 # Database migrations
├── docs/                    # Documentation
├── docker-compose.yml       # Container orchestration
├── Dockerfile               # Backend container
├── requirements.txt         # Python dependencies
├── test_api.py              # Python test suite
├── curl_tests.sh            # Bash test script
└── curl_tests.ps1           # PowerShell test script
```

## 🔧 Configuration

Environment variables (`.env` file):

```env
DATABASE_URL=postgresql+asyncpg://kyros:kyros@localhost:5432/kyros
SECRET_KEY=your-secret-key-here
DEBUG=true
```

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

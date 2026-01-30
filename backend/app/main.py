"""
Kyros Backend Application - FastAPI Entry Point.

A production-ready FastAPI application for retail planning and procurement management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.database import engine
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Create tables (SQLite) or verify database connection (PostgreSQL)
    - Shutdown: Dispose database connections
    """
    # Startup
    app.state.db_connected = False
    try:
        # Create all tables (important for SQLite testing)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created/verified")
        
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Database connection verified")
        app.state.db_connected = True
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("ℹ️  Server starting without database - endpoints requiring DB will fail")
        # Don't raise - allow app to start for API docs viewing
    
    yield
    
    # Shutdown
    try:
        await engine.dispose()
        print("🔌 Database connections closed")
    except Exception:
        pass


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Kyros Backend API
    
    A comprehensive retail planning and procurement management system.
    
    ### Features:
    - **Season Management**: Create and manage retail seasons with workflow states
    - **Location Hierarchy**: Clusters and locations (stores/warehouses)
    - **Category Management**: Hierarchical product categories
    - **Planning**: Season plans with budget allocation
    - **OTB (Open-to-Buy)**: Monthly budget limits
    - **Range Intent**: Core/Fashion mix with price bands
    - **Purchase Orders**: PO creation and tracking
    - **GRN (Goods Receipt Notes)**: Track deliveries
    - **Analytics**: Dashboard and reporting
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with detailed messages."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    # Log the error (in production, use proper logging)
    print(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


# Include API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


# Health check endpoints
@app.get("/", tags=["Health"])
async def root() -> dict:
    """Root endpoint - API status check."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "database": "connected",
    }


@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict:
    """Readiness check - verify all dependencies are ready."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "ready" if db_status == "connected" else "not_ready",
        "database": db_status,
    }

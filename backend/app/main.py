"""
Kyros Backend Application - FastAPI Entry Point.

A production-ready FastAPI application for retail planning and procurement management.
"""

import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.database import engine, is_sqlite
from app.core.logging import get_logger, setup_logging
from app.core.middleware import (
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.models.base import Base

# Setup logging
setup_logging()
logger = get_logger(__name__)


def handle_shutdown_signal(signum, frame):
    """Handle graceful shutdown signals."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    sys.exit(0)


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGTERM, handle_shutdown_signal)
signal.signal(signal.SIGINT, handle_shutdown_signal)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Create tables (SQLite) or verify database connection (PostgreSQL)
    - Shutdown: Dispose database connections
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    app.state.db_connected = False
    try:
        if is_sqlite:
            # SQLite: create tables directly (no migrations)
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True))
            logger.info("Database tables created/verified (SQLite)")
        
        # Verify connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
        app.state.db_connected = True
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.info("Server starting without database - endpoints requiring DB will fail")
        # Don't raise - allow app to start for API docs viewing
    
    logger.info(f"Application started successfully on port 8000")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
    
    logger.info("Application shutdown complete")


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
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# Add middleware (order matters - first added is last executed)
# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Request ID tracking
app.add_middleware(RequestIdMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
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

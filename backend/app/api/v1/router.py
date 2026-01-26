"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    categories,
    clusters,
    grn,
    locations,
    otb,
    plans,
    po,
    range_intent,
    seasons,
    users,
)

router = APIRouter()

# User management
router.include_router(users.router)

# Season management
router.include_router(seasons.router)

# Location hierarchy
router.include_router(clusters.router)
router.include_router(locations.router)

# Category management
router.include_router(categories.router)

# Planning & Budgeting
router.include_router(plans.router)
router.include_router(otb.router)
router.include_router(range_intent.router)

# Procurement
router.include_router(po.router)
router.include_router(grn.router)

# Analytics & Reporting
router.include_router(analytics.router)

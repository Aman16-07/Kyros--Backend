"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    analytics,
    auth,
    categories,
    clusters,
    grn,
    locations,
    otb,
    otb_management,
    plans,
    po,
    range_architecture,
    range_intent,
    seasons,
    users,
)

router = APIRouter()

# Authentication (no prefix - /api/v1/auth)
router.include_router(auth.router)

# System Administration (super admin only)
router.include_router(admin.router)

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

# Phase 2: OTB Management & Range Architecture
router.include_router(otb_management.router)
router.include_router(range_architecture.router)

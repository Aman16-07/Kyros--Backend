"""System Administration API endpoints for super admins."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_super_admin
from app.models.user import User, UserRole
from app.models.company import CompanyStatus
from app.repositories.company_repo import CompanyRepository
from app.repositories.user_repo import UserRepository
from app.schemas.company import (
    CompanyApproval,
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.schemas.base import MessageResponse

router = APIRouter(prefix="/admin", tags=["System Administration"])


# =============================================================================
# Company Management Endpoints (Super Admin Only)
# =============================================================================

@router.get(
    "/companies",
    response_model=CompanyListResponse,
    summary="List all companies",
    description="Get a paginated list of all companies (super admin only).",
)
async def list_companies(
    status: Optional[CompanyStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """List all companies with optional status filter."""
    repo = CompanyRepository(db)
    
    if status:
        companies, total = await repo.list_by_status(status, skip, limit)
    else:
        companies, total = await repo.list_all(skip, limit)
    
    return CompanyListResponse(items=companies, total=total)


@router.get(
    "/companies/pending",
    response_model=CompanyListResponse,
    summary="List pending company requests",
    description="Get all pending company registration requests awaiting approval.",
)
async def list_pending_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """List pending company registration requests."""
    repo = CompanyRepository(db)
    companies, total = await repo.list_pending(skip, limit)
    
    return CompanyListResponse(items=companies, total=total)


@router.get(
    "/companies/{company_id}",
    response_model=CompanyResponse,
    summary="Get company details",
    description="Get detailed information about a specific company.",
)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Get company by ID."""
    repo = CompanyRepository(db)
    company = await repo.get(company_id)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    return company


@router.post(
    "/companies/{company_id}/approve",
    response_model=CompanyResponse,
    summary="Approve company request",
    description="Approve a pending company registration request.",
)
async def approve_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Approve a pending company request and activate the admin user."""
    company_repo = CompanyRepository(db)
    user_repo = UserRepository(db)
    
    # Approve company (this also generates the 8-digit code)
    company = await company_repo.approve(company_id, current_user.id)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company not found or not in pending status",
        )
    
    # Activate all users belonging to this company
    company_users = await user_repo.list_by_company(str(company_id))
    for user in company_users:
        if not user.is_active:
            user.is_active = True
            user.company_code = company.code  # Set the generated code
    
    await db.commit()
    await db.refresh(company)
    
    return company


@router.post(
    "/companies/{company_id}/reject",
    response_model=CompanyResponse,
    summary="Reject company request",
    description="Reject a pending company registration request.",
)
async def reject_company(
    company_id: UUID,
    data: CompanyApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Reject a pending company request."""
    if not data.reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required",
        )
    
    repo = CompanyRepository(db)
    company = await repo.reject(company_id, data.reason)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company not found or not in pending status",
        )
    
    return company


@router.post(
    "/companies/{company_id}/suspend",
    response_model=CompanyResponse,
    summary="Suspend company",
    description="Suspend an approved company.",
)
async def suspend_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Suspend an approved company."""
    repo = CompanyRepository(db)
    company = await repo.suspend(company_id)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company not found or not in approved status",
        )
    
    return company


@router.post(
    "/companies/{company_id}/reactivate",
    response_model=CompanyResponse,
    summary="Reactivate company",
    description="Reactivate a suspended company.",
)
async def reactivate_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Reactivate a suspended company."""
    repo = CompanyRepository(db)
    company = await repo.reactivate(company_id)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company not found or not in suspended status",
        )
    
    return company


# =============================================================================
# User Management Endpoints (Super Admin Only)
# =============================================================================

@router.get(
    "/users",
    summary="List all users",
    description="Get a paginated list of all users across all companies.",
)
async def list_all_users(
    company_id: Optional[UUID] = Query(None, description="Filter by company"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """List all users with filters."""
    repo = UserRepository(db)
    users, total = await repo.list_all_users(
        company_id=company_id,
        role=role,
        skip=skip,
        limit=limit,
    )
    
    return {"items": users, "total": total}


@router.post(
    "/users/{user_id}/make-admin",
    response_model=MessageResponse,
    summary="Make user a company admin",
    description="Promote a user to company admin role.",
)
async def make_user_admin(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Promote user to admin."""
    repo = UserRepository(db)
    user = await repo.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify super admin role",
        )
    
    await repo.update(user_id, {"role": UserRole.ADMIN})
    
    return MessageResponse(message=f"User {user.name} is now a company admin")


@router.post(
    "/users/{user_id}/deactivate",
    response_model=MessageResponse,
    summary="Deactivate user",
    description="Deactivate a user account.",
)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Deactivate a user."""
    repo = UserRepository(db)
    user = await repo.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate super admin",
        )
    
    await repo.update(user_id, {"is_active": False})
    
    return MessageResponse(message=f"User {user.name} has been deactivated")


@router.post(
    "/users/{user_id}/activate",
    response_model=MessageResponse,
    summary="Activate user",
    description="Reactivate a deactivated user account.",
)
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Activate a user."""
    repo = UserRepository(db)
    user = await repo.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    await repo.update(user_id, {"is_active": True})
    
    return MessageResponse(message=f"User {user.name} has been activated")


# =============================================================================
# System Statistics (Super Admin Only)
# =============================================================================

@router.get(
    "/stats",
    summary="Get system statistics",
    description="Get overall system statistics for the admin dashboard.",
)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Get system-wide statistics."""
    company_repo = CompanyRepository(db)
    user_repo = UserRepository(db)
    
    # Get company counts by status
    _, pending_count = await company_repo.list_by_status(CompanyStatus.PENDING)
    _, approved_count = await company_repo.list_by_status(CompanyStatus.APPROVED)
    _, rejected_count = await company_repo.list_by_status(CompanyStatus.REJECTED)
    _, suspended_count = await company_repo.list_by_status(CompanyStatus.SUSPENDED)
    
    total_companies = pending_count + approved_count + rejected_count + suspended_count
    total_users = await user_repo.count_all()
    
    return {
        "total_companies": total_companies,
        "pending_companies": pending_count,
        "approved_companies": approved_count,
        "rejected_companies": rejected_count,
        "suspended_companies": suspended_count,
        "total_users": total_users,
    }

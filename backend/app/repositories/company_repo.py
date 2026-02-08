"""Company repository for database operations."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_company_code
from app.models.company import Company, CompanyStatus
from app.repositories.base_repo import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Repository for Company model operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Company, db)
    
    async def get_by_code(self, code: str) -> Optional[Company]:
        """Get a company by its unique code."""
        result = await self.session.execute(
            select(Company).where(Company.code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Company]:
        """Get a company by name."""
        result = await self.session.execute(
            select(Company).where(Company.name == name)
        )
        return result.scalar_one_or_none()
    
    async def list_by_status(
        self, 
        status: CompanyStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Company], int]:
        """List companies by status with pagination."""
        # Count query
        count_query = select(func.count()).select_from(Company).where(
            Company.status == status
        )
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0
        
        # Data query
        query = (
            select(Company)
            .where(Company.status == status)
            .order_by(Company.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        companies = list(result.scalars().all())
        
        return companies, total_count
    
    async def list_pending(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Company], int]:
        """List pending company requests."""
        return await self.list_by_status(CompanyStatus.PENDING, skip, limit)
    
    async def approve(
        self,
        company_id: UUID,
        approved_by: UUID,
    ) -> Optional[Company]:
        """Approve a pending company request and generate the 8-digit code."""
        company = await self.get(company_id)
        if not company:
            return None
        
        if company.status != CompanyStatus.PENDING:
            return None
        
        # Generate unique 8-digit code on approval
        company.code = generate_company_code()
        company.status = CompanyStatus.APPROVED
        company.approved_at = datetime.now(timezone.utc)
        company.approved_by = str(approved_by)
        
        await self.session.commit()
        await self.session.refresh(company)
        return company
    
    async def reject(
        self,
        company_id: UUID,
        reason: str,
    ) -> Optional[Company]:
        """Reject a pending company request."""
        company = await self.get(company_id)
        if not company:
            return None
        
        if company.status != CompanyStatus.PENDING:
            return None
        
        company.status = CompanyStatus.REJECTED
        company.rejected_at = datetime.now(timezone.utc)
        company.rejected_reason = reason
        
        await self.session.commit()
        await self.session.refresh(company)
        return company
    
    async def suspend(self, company_id: UUID) -> Optional[Company]:
        """Suspend an approved company."""
        company = await self.get(company_id)
        if not company:
            return None
        
        if company.status != CompanyStatus.APPROVED:
            return None
        
        company.status = CompanyStatus.SUSPENDED
        
        await self.session.commit()
        await self.session.refresh(company)
        return company
    
    async def reactivate(self, company_id: UUID) -> Optional[Company]:
        """Reactivate a suspended company."""
        company = await self.get(company_id)
        if not company:
            return None
        
        if company.status != CompanyStatus.SUSPENDED:
            return None
        
        company.status = CompanyStatus.APPROVED
        
        await self.session.commit()
        await self.session.refresh(company)
        return company

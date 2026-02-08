"""Company schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.models.company import CompanyStatus
from app.schemas.base import BaseSchema, TimestampMixin, UUIDMixin


class CompanyBase(BaseSchema):
    """Base company schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    contact_email: EmailStr


class CompanyCreate(CompanyBase):
    """Schema for creating a company (registration request)."""
    
    domain: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, description="Requester notes for approval")


class CompanyUpdate(BaseSchema):
    """Schema for updating a company."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=100)


class CompanyApproval(BaseSchema):
    """Schema for approving/rejecting a company."""
    
    approved: bool
    reason: Optional[str] = Field(None, description="Required if rejecting")


class CompanyResponse(CompanyBase, UUIDMixin, TimestampMixin):
    """Schema for company response."""
    
    code: Optional[str] = Field(None, description="8-digit unique company code (generated on approval)")
    domain: Optional[str] = None
    tax_id: Optional[str] = None
    status: CompanyStatus
    notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    rejected_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None


class CompanyListResponse(BaseSchema):
    """Schema for list of companies."""
    
    items: list[CompanyResponse]
    total: int


class PendingCompanyResponse(CompanyResponse):
    """Schema for pending company with requester info."""
    
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None

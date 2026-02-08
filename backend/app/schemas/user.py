"""User and authentication schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.base import BaseSchema, TimestampMixin, UUIDMixin


# =============================================================================
# User Base Schemas
# =============================================================================

class UserBase(BaseSchema):
    """Base user schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr = Field(..., description="User's email address")


class UserCreate(UserBase):
    """Schema for creating a user (admin only)."""
    
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = Field(default=UserRole.VIEWER)
    company_name: Optional[str] = Field(None, max_length=255)
    company_code: Optional[str] = Field(None, max_length=50)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    company_name: Optional[str] = Field(None, max_length=255)


class UserResponse(BaseSchema, UUIDMixin, TimestampMixin):
    """Schema for user response (excludes sensitive data)."""
    
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    is_verified: bool
    company_name: Optional[str] = None
    company_code: Optional[str] = None
    last_login_at: Optional[datetime] = None


class UserListResponse(BaseSchema):
    """Schema for list of users."""
    
    items: list[UserResponse]
    total: int


# =============================================================================
# Authentication Schemas
# =============================================================================

class LoginRequest(BaseModel):
    """Schema for login request."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")


class RegisterRequest(BaseModel):
    """Schema for user registration."""
    
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=100)
    company_name: Optional[str] = Field(None, max_length=255, description="Company name for new company registration")
    company_code: Optional[str] = Field(None, max_length=50, description="Company code to join existing company")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class TokenResponse(BaseModel):
    """Schema for token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class AuthResponse(BaseModel):
    """Schema for authentication response (login/register)."""
    
    user: UserResponse
    tokens: TokenResponse


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    
    refresh_token: str = Field(..., description="JWT refresh token")


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(..., description="User's email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""
    
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class MessageResponse(BaseModel):
    """Simple message response."""
    
    message: str
    success: bool = True


# =============================================================================
# Company Registration Schemas
# =============================================================================

class CompanyRegisterRequest(BaseModel):
    """Schema for registering a new company (requires admin approval)."""
    
    # User info
    name: str = Field(..., min_length=1, max_length=255, description="Admin user's full name")
    email: EmailStr = Field(..., description="Admin user's email address")
    password: str = Field(..., min_length=8, max_length=100)
    
    # Company info
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    company_email: Optional[EmailStr] = Field(None, description="Company contact email (defaults to user email)")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes for the admin")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class CompanyRegisterResponse(BaseModel):
    """Response after company registration request."""
    
    message: str
    company_name: str
    status: str = "pending"
    success: bool = True


class JoinCompanyRequest(BaseModel):
    """Schema for joining an existing company."""
    
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=100)
    company_code: str = Field(..., min_length=8, max_length=8, description="8-digit company code")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

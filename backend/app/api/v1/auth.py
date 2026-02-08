"""Authentication API endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.deps import DBSession
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    generate_company_code,
    hash_password,
    verify_email_verification_token,
    verify_password_reset_token,
    verify_refresh_token,
)
from app.models.audit_log import AuditAction, AuditLog
from app.models.user import User, UserRole
from app.models.company import Company, CompanyStatus
from app.repositories.user_repo import UserRepository
from app.repositories.company_repo import CompanyRepository
from app.schemas.user import (
    AuthResponse,
    ChangePasswordRequest,
    CompanyRegisterRequest,
    CompanyRegisterResponse,
    JoinCompanyRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit_service import AuditService
from app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme for JWT
security = HTTPBearer(auto_error=False)


def _create_tokens(user_id: UUID) -> TokenResponse:
    """Create access and refresh tokens for a user."""
    access_token = create_access_token(
        subject=user_id,
        additional_claims={"type": "access"},
    )
    refresh_token = create_refresh_token(subject=user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def _log_failed_login(
    db: DBSession,
    email: str,
    reason: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    user_id: UUID | None = None,
) -> None:
    """Log a failed login attempt for security auditing."""
    audit = AuditService(db)
    # Use a dummy UUID for entity_id since we may not have a user
    entity_id = user_id or uuid4()
    log_entry = AuditLog(
        entity_type="User",
        entity_id=entity_id,
        action=AuditAction.LOGIN,
        user_id=user_id,
        new_data={
            "email": email,
            "success": False,
            "reason": reason,
        },
        description=f"Failed login attempt: {reason}",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log_entry)
    await db.flush()


@router.post(
    "/register-company",
    response_model=CompanyRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new company",
    description="Register a new company. Requires admin approval before users can log in.",
)
async def register_company(
    data: CompanyRegisterRequest,
    db: DBSession,
) -> CompanyRegisterResponse:
    """
    Register a new company with admin user.
    
    - Creates a pending company registration
    - Creates an inactive admin user linked to the company
    - Sends verification email to the user
    - User cannot login until company is approved by system admin
    - Upon approval, 8-digit company code is generated
    """
    user_repo = UserRepository(db)
    company_repo = CompanyRepository(db)
    email_service = EmailService()
    
    # Check if email already exists
    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    
    # Check if company name already exists
    existing_company = await company_repo.get_by_name(data.company_name)
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A company with this name already exists",
        )
    
    # Create pending company (no code yet - generated on approval)
    company = await company_repo.create(
        name=data.company_name,
        contact_email=data.company_email or data.email,
        notes=data.notes,
        status=CompanyStatus.PENDING,
    )
    
    # Create the admin user (inactive until company is approved)
    user = await user_repo.create(
        name=data.name,
        email=data.email,
        password=data.password,
        role=UserRole.ADMIN,
        company_id=str(company.id),
        company_name=data.company_name,
        is_active=False,  # Cannot login until approved
    )
    
    # Send verification email
    verification_token = create_email_verification_token(data.email)
    await email_service.send_verification_email(
        to_email=data.email,
        user_name=data.name,
        verification_token=verification_token,
    )
    
    return CompanyRegisterResponse(
        message="Your company registration is under review. Please check your email to verify your address. We will notify you once approved.",
        company_name=data.company_name,
        status="pending",
        success=True,
    )


@router.post(
    "/join-company",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join an existing company",
    description="Register as a new user and join an approved company using the 8-digit company code.",
)
async def join_company(
    data: JoinCompanyRequest,
    db: DBSession,
) -> AuthResponse:
    """
    Join an existing approved company.
    
    - User provides the 8-digit company code
    - User is immediately registered and can login
    - No admin approval needed for joining
    """
    user_repo = UserRepository(db)
    company_repo = CompanyRepository(db)
    
    # Check if email already exists
    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    
    # Find company by code
    company = await company_repo.get_by_code(data.company_code)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid company code. Please check and try again.",
        )
    
    # Check if company is approved
    if company.status != CompanyStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This company is not active. Please contact your company administrator.",
        )
    
    # Create the user as VIEWER under this company
    user = await user_repo.create(
        name=data.name,
        email=data.email,
        password=data.password,
        role=UserRole.VIEWER,
        company_id=str(company.id),
        company_name=company.name,
        company_code=company.code,
        is_active=True,
    )
    
    # Create tokens
    tokens = _create_tokens(user.id)
    
    # Store refresh token hash
    await user_repo.set_refresh_token(user.id, hash_password(tokens.refresh_token))
    
    # Update last login
    await user_repo.update_last_login(user.id)
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
    )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address",
    description="Verify user's email address using the token sent during registration.",
)
async def verify_email(
    token: str,
    db: DBSession,
) -> MessageResponse:
    """
    Verify user's email address.
    
    - Validates the verification token
    - Marks the user as verified (is_verified = True)
    - User still needs company approval to login
    """
    user_repo = UserRepository(db)
    
    # Verify the token
    email = verify_email_verification_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token. Please request a new one.",
        )
    
    # Find the user
    user = await user_repo.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    # Check if already verified
    if user.is_verified:
        return MessageResponse(message="Email already verified.")
    
    # Mark user as verified
    await user_repo.update(user.id, is_verified=True)
    
    return MessageResponse(message="Email verified successfully. Please wait for company approval to login.")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
    description="Resend the email verification link to the user's email address.",
)
async def resend_verification(
    email: str,
    db: DBSession,
) -> MessageResponse:
    """
    Resend verification email.
    
    - Generates a new verification token
    - Sends verification email
    """
    user_repo = UserRepository(db)
    email_service = EmailService()
    
    # Find the user
    user = await user_repo.get_by_email(email)
    if not user:
        # Don't reveal if email exists
        return MessageResponse(message="If an account with this email exists, a verification link has been sent.")
    
    # Check if already verified
    if user.is_verified:
        return MessageResponse(message="Email already verified.")
    
    # Generate new verification token and send email
    verification_token = create_email_verification_token(email)
    await email_service.send_verification_email(
        to_email=email,
        user_name=user.name,
        verification_token=verification_token,
    )
    
    return MessageResponse(message="Verification email sent. Please check your inbox.")


# Keep old register endpoint for backward compatibility but deprecate it
@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[DEPRECATED] Register a new user",
    description="Use /register-company to create a new company or /join-company to join an existing one.",
    deprecated=True,
)
async def register(
    data: RegisterRequest,
    db: DBSession,
) -> AuthResponse:
    """
    [DEPRECATED] Register a new user.
    Use /register-company or /join-company instead.
    """
    # Redirect to join-company if company_code is provided
    if data.company_code:
        join_data = JoinCompanyRequest(
            name=data.name,
            email=data.email,
            password=data.password,
            company_code=data.company_code,
        )
        return await join_company(join_data, db)
    
    # For new company registration, return error
    if data.company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please use /auth/register-company to create a new company",
        )
    
    # No company - just create user without company
    repo = UserRepository(db)
    existing_user = await repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    
    user = await repo.create(
        name=data.name,
        email=data.email,
        password=data.password,
        role=UserRole.ADMIN,  # Deprecated endpoint - grant admin for dev/testing
    )
    
    tokens = _create_tokens(user.id)
    await repo.set_refresh_token(user.id, hash_password(tokens.refresh_token))
    await repo.update_last_login(user.id)
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login to get access token",
    description="Authenticate with email and password to receive JWT tokens.",
)
async def login(
    data: LoginRequest,
    db: DBSession,
    request: Request,
) -> AuthResponse:
    """
    Authenticate a user and return tokens.
    """
    repo = UserRepository(db)
    company_repo = CompanyRepository(db)
    
    # Extract IP and User-Agent for audit logging
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    # Authenticate user
    user = await repo.authenticate(data.email, data.password)
    if user is None:
        # Log failed login attempt
        await _log_failed_login(
            db=db,
            email=data.email,
            reason="Invalid email or password",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active (users with pending companies are inactive)
    if not user.is_active:
        # Check if user has a company and its status
        if user.company_id:
            company = await company_repo.get(UUID(user.company_id))
            if company and company.status == CompanyStatus.PENDING:
                await _log_failed_login(
                    db=db,
                    email=data.email,
                    reason="Company pending approval",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    user_id=user.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your company registration is still under review. We will notify you once approved.",
                )
            elif company and company.status == CompanyStatus.REJECTED:
                await _log_failed_login(
                    db=db,
                    email=data.email,
                    reason="Company rejected",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    user_id=user.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your company registration was rejected. Please contact support for more information.",
                )
            elif company and company.status == CompanyStatus.SUSPENDED:
                await _log_failed_login(
                    db=db,
                    email=data.email,
                    reason="Company suspended",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    user_id=user.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your company has been suspended. Please contact support.",
                )
        await _log_failed_login(
            db=db,
            email=data.email,
            reason="Account inactive",
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive. Please contact support.",
        )
    
    # Create tokens
    tokens = _create_tokens(user.id)
    
    # Store refresh token hash
    await repo.set_refresh_token(user.id, hash_password(tokens.refresh_token))
    
    # Update last login
    await repo.update_last_login(user.id)
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use a valid refresh token to get a new access token.",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: DBSession,
) -> TokenResponse:
    """
    Refresh the access token using a valid refresh token.
    """
    # Verify refresh token
    user_id = verify_refresh_token(data.refresh_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    tokens = _create_tokens(user.id)
    
    # Update refresh token hash
    await repo.set_refresh_token(user.id, hash_password(tokens.refresh_token))
    
    return tokens


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Invalidate the current refresh token.",
)
async def logout(
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> MessageResponse:
    """
    Logout the current user by invalidating their refresh token.
    """
    if credentials is None:
        return MessageResponse(message="Logged out successfully")
    
    from app.core.security import verify_access_token
    
    user_id = verify_access_token(credentials.credentials)
    if user_id:
        repo = UserRepository(db)
        await repo.clear_refresh_token(UUID(user_id))
    
    return MessageResponse(message="Logged out successfully")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Request a password reset link to be sent to the user's email.",
)
async def forgot_password(
    data: PasswordResetRequest,
    db: DBSession,
) -> MessageResponse:
    """
    Request a password reset.
    
    For security, always returns success even if email doesn't exist.
    """
    repo = UserRepository(db)
    user = await repo.get_by_email(data.email)
    
    if user:
        # Generate reset token
        token = create_password_reset_token(data.email)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Store token in database
        await repo.set_password_reset_token(user.id, token, expires)
        
        # TODO: Send email with reset link
        # In production, integrate with email service
        # For now, log the token (remove in production!)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Password reset token for {data.email}: {token}")
    
    return MessageResponse(
        message="If an account with this email exists, a password reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token",
    description="Reset password using the token received via email.",
)
async def reset_password(
    data: PasswordResetConfirm,
    db: DBSession,
) -> MessageResponse:
    """
    Reset password using a valid reset token.
    """
    # Verify token
    email = verify_password_reset_token(data.token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    repo = UserRepository(db)
    user = await repo.get_by_reset_token(data.token)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    # Update password
    await repo.update_password(user.id, data.new_password)
    
    # Clear all refresh tokens (force re-login on all devices)
    await repo.clear_refresh_token(user.id)
    
    return MessageResponse(message="Password has been reset successfully")


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change password for authenticated user.",
)
async def change_password(
    data: ChangePasswordRequest,
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> MessageResponse:
    """
    Change password for the authenticated user.
    """
    from app.core.security import verify_access_token, verify_password
    
    user_id = verify_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Verify current password
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    # Update password
    await repo.update_password(user.id, data.new_password)
    
    # Clear refresh tokens (force re-login)
    await repo.clear_refresh_token(user.id)
    
    return MessageResponse(message="Password changed successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile.",
)
async def get_current_user(
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> UserResponse:
    """
    Get the current authenticated user's profile.
    """
    from app.core.security import verify_access_token
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = verify_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse.model_validate(user)

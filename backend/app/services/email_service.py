"""Email service for sending verification and password reset emails.

This module provides email functionality for:
- Email verification after registration
- Password reset emails
- Welcome emails after company approval

In production, this should be configured with a real SMTP server
or email service provider (e.g., SendGrid, AWS SES, Mailgun).
"""

import logging
from typing import Optional

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails.
    
    In development mode, emails are logged to console.
    In production, configure SMTP settings in environment variables.
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
    ):
        """Initialize email service with SMTP settings."""
        self.smtp_host = smtp_host or getattr(settings, 'SMTP_HOST', None)
        self.smtp_port = smtp_port or getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = smtp_user or getattr(settings, 'SMTP_USER', None)
        self.smtp_password = smtp_password or getattr(settings, 'SMTP_PASSWORD', None)
        self.from_email = from_email or getattr(settings, 'FROM_EMAIL', 'noreply@kyros.com')
        
        # Check if email is configured
        self.is_configured = bool(self.smtp_host and self.smtp_user)
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email.
        
        In development mode, logs the email content.
        In production with SMTP configured, sends via SMTP.
        
        Returns True if email was sent/logged successfully.
        """
        if not self.is_configured:
            # Development mode - log email
            logger.info(f"""
=== EMAIL (Development Mode) ===
To: {to_email}
Subject: {subject}
---
{body_text or body_html}
================================
""")
            return True
        
        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            if body_text:
                message.attach(MIMEText(body_text, "plain"))
            message.attach(MIMEText(body_html, "html"))
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True,
            )
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except ImportError:
            logger.warning("aiosmtplib not installed. Install with: pip install aiosmtplib")
            logger.info(f"Email would be sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_token: str,
        verification_url: Optional[str] = None,
    ) -> bool:
        """
        Send email verification link to new user.
        
        Args:
            to_email: User's email address
            user_name: User's display name
            verification_token: Token for email verification
            verification_url: Base URL for verification (defaults to frontend URL)
        
        Returns True if email was sent successfully.
        """
        base_url = verification_url or getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verify_link = f"{base_url}/verify-email?token={verification_token}"
        
        subject = "Verify your KYROS account"
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; background: #2563eb; color: white; padding: 12px 24px; 
                   text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to KYROS</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>Thank you for registering with KYROS. Please verify your email address to complete your registration.</p>
            <p><a href="{verify_link}" class="button">Verify Email Address</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p><small>{verify_link}</small></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account with KYROS, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; KYROS - Retail Planning Platform</p>
        </div>
    </div>
</body>
</html>
"""
        
        body_text = f"""
Hello {user_name},

Thank you for registering with KYROS. Please verify your email address to complete your registration.

Click this link to verify your email:
{verify_link}

This link will expire in 24 hours.

If you didn't create an account with KYROS, please ignore this email.

KYROS - Retail Planning Platform
"""
        
        return await self._send_email(to_email, subject, body_html, body_text)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_token: str,
        reset_url: Optional[str] = None,
    ) -> bool:
        """
        Send password reset link to user.
        
        Args:
            to_email: User's email address
            user_name: User's display name
            reset_token: Token for password reset
            reset_url: Base URL for password reset (defaults to frontend URL)
        
        Returns True if email was sent successfully.
        """
        base_url = reset_url or getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{base_url}/reset-password?token={reset_token}"
        
        subject = "Reset your KYROS password"
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; background: #2563eb; color: white; padding: 12px 24px; 
                   text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .warning {{ background: #fef3c7; padding: 15px; border-radius: 4px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>KYROS Password Reset</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>We received a request to reset your password. Click the button below to set a new password:</p>
            <p><a href="{reset_link}" class="button">Reset Password</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p><small>{reset_link}</small></p>
            <div class="warning">
                <strong>This link will expire in 1 hour.</strong>
            </div>
            <p>If you didn't request a password reset, please ignore this email or contact support if you're concerned about your account security.</p>
        </div>
        <div class="footer">
            <p>&copy; KYROS - Retail Planning Platform</p>
        </div>
    </div>
</body>
</html>
"""
        
        body_text = f"""
Hello {user_name},

We received a request to reset your password. Click the link below to set a new password:

{reset_link}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email or contact support if you're concerned about your account security.

KYROS - Retail Planning Platform
"""
        
        return await self._send_email(to_email, subject, body_html, body_text)
    
    async def send_company_approved_email(
        self,
        to_email: str,
        user_name: str,
        company_name: str,
        company_code: str,
    ) -> bool:
        """
        Send notification that company registration has been approved.
        
        Args:
            to_email: Admin user's email address
            user_name: Admin user's display name
            company_name: Name of the approved company
            company_code: Assigned 8-digit company code
        
        Returns True if email was sent successfully.
        """
        login_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000') + '/login'
        
        subject = f"Your company {company_name} has been approved!"
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #059669; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; background: #2563eb; color: white; padding: 12px 24px; 
                   text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .code-box {{ background: #e0e7ff; padding: 20px; border-radius: 8px; text-align: center; 
                     margin: 20px 0; }}
        .code {{ font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 4px; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Congratulations!</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>Great news! Your company <strong>{company_name}</strong> has been approved to use KYROS.</p>
            <p>Your unique company code is:</p>
            <div class="code-box">
                <span class="code">{company_code}</span>
            </div>
            <p>Share this code with your team members so they can join your organization during registration.</p>
            <p>You can now log in and start using KYROS:</p>
            <p><a href="{login_url}" class="button">Log In to KYROS</a></p>
        </div>
        <div class="footer">
            <p>&copy; KYROS - Retail Planning Platform</p>
        </div>
    </div>
</body>
</html>
"""
        
        body_text = f"""
Hello {user_name},

Great news! Your company {company_name} has been approved to use KYROS.

Your unique company code is: {company_code}

Share this code with your team members so they can join your organization during registration.

You can now log in and start using KYROS:
{login_url}

KYROS - Retail Planning Platform
"""
        
        return await self._send_email(to_email, subject, body_html, body_text)
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
        company_name: str,
    ) -> bool:
        """
        Send welcome email to new team member who joined via company code.
        
        Args:
            to_email: User's email address
            user_name: User's display name
            company_name: Name of the company they joined
        
        Returns True if email was sent successfully.
        """
        login_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000') + '/login'
        
        subject = f"Welcome to {company_name} on KYROS!"
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f9fafb; }}
        .button {{ display: inline-block; background: #2563eb; color: white; padding: 12px 24px; 
                   text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to KYROS!</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>You've successfully joined <strong>{company_name}</strong> on KYROS.</p>
            <p>You can now access the retail planning platform and collaborate with your team.</p>
            <p><a href="{login_url}" class="button">Log In to KYROS</a></p>
        </div>
        <div class="footer">
            <p>&copy; KYROS - Retail Planning Platform</p>
        </div>
    </div>
</body>
</html>
"""
        
        body_text = f"""
Hello {user_name},

You've successfully joined {company_name} on KYROS.

You can now access the retail planning platform and collaborate with your team.

Log in at: {login_url}

KYROS - Retail Planning Platform
"""
        
        return await self._send_email(to_email, subject, body_html, body_text)


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the email service singleton instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

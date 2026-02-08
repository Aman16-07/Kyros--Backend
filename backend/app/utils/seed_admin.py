"""Seed script to create the initial super admin user."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.user import User, UserRole


async def seed_super_admin():
    """Create the initial super admin user if not exists."""
    
    admin_email = "admin@aexiz.com"
    admin_password = "qwerty123"
    admin_name = "System Administrator"
    
    async with async_session_factory() as session:
        # Check if admin already exists
        result = await session.execute(
            select(User).where(User.email == admin_email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if existing_user.role == UserRole.SUPER_ADMIN:
                print(f"✓ Super admin already exists: {admin_email}")
            else:
                # Upgrade to super admin
                existing_user.role = UserRole.SUPER_ADMIN
                await session.commit()
                print(f"✓ Upgraded existing user to super admin: {admin_email}")
            return
        
        # Create new super admin user
        hashed_password = hash_password(admin_password)
        
        admin_user = User(
            name=admin_name,
            email=admin_email,
            password_hash=hashed_password,
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )
        
        session.add(admin_user)
        await session.commit()
        
        print(f"✓ Super admin created successfully!")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")
        print(f"  Role: super_admin")


if __name__ == "__main__":
    asyncio.run(seed_super_admin())

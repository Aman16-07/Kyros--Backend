"""Add authentication fields to users table.

Revision ID: 001_auth_fields
Revises: 
Create Date: 2026-02-01

This migration adds the following fields to the users table:
- email (unique, indexed)
- password_hash
- is_active
- is_verified
- company_name
- company_code
- last_login_at
- password_reset_token
- password_reset_expires
- refresh_token_hash
- updated_at
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_auth_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add authentication fields to users table."""
    # Create users table with all fields if it doesn't exist
    # This handles fresh installations
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'manager', 'viewer', name='user_role', create_type=True), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('company_code', sa.String(50), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refresh_token_hash', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        if_not_exists=True
    )
    
    # Create indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=True, if_not_exists=True)
    op.create_index('ix_users_company_code', 'users', ['company_code'], if_not_exists=True)


def downgrade() -> None:
    """Remove users table."""
    op.drop_index('ix_users_company_code', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS user_role')

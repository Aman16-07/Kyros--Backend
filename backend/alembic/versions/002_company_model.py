"""Add company model and update user model

Revision ID: 002_company_model
Revises: 001_auth_fields
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_company_model'
down_revision = '001_auth_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create company_status enum
    company_status = postgresql.ENUM(
        'pending', 'approved', 'rejected', 'suspended',
        name='company_status',
        create_type=False
    )
    company_status.create(op.get_bind(), checkfirst=True)
    
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(8), nullable=False, unique=True, index=True),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('tax_id', sa.String(100), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', 'suspended', name='company_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Add company_id to users table
    op.add_column('users', sa.Column('company_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_users_company_id',
        'users', 'companies',
        ['company_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Update user_role enum to add super_admin
    # First, we need to alter the enum type
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'super_admin'")


def downgrade() -> None:
    # Remove company_id from users
    op.drop_constraint('fk_users_company_id', 'users', type_='foreignkey')
    op.drop_column('users', 'company_id')
    
    # Drop companies table
    op.drop_table('companies')
    
    # Drop company_status enum
    op.execute("DROP TYPE IF EXISTS company_status")

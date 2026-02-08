"""Add audit_logs table and missing model fields.

Revision ID: 006_audit_and_fields
Revises: 005_po_new_fields
Create Date: 2026-02-02

This migration:
1. Creates the audit_logs table for tracking all system changes
2. Adds missing fields to season_plan: sku_id, planned_units, ly_sales, lly_sales
3. Adds missing fields to locations: address, city, state, country, postal_code, is_active
4. Updates unique constraint on season_plan to include sku_id
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_audit_and_fields'
down_revision = '005_po_new_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_action enum type
    audit_action_enum = postgresql.ENUM(
        'create', 'update', 'delete', 'approve', 'lock', 'unlock',
        'login', 'logout', 'upload', 'workflow_transition',
        name='audit_action',
        create_type=False
    )
    audit_action_enum.create(op.get_bind(), checkfirst=True)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(100), nullable=False, index=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('action', postgresql.ENUM(
            'create', 'update', 'delete', 'approve', 'lock', 'unlock',
            'login', 'logout', 'upload', 'workflow_transition',
            name='audit_action',
            create_type=False
        ), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('old_data', postgresql.JSONB, nullable=True),
        sa.Column('new_data', postgresql.JSONB, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('season_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seasons.id', ondelete='SET NULL'), nullable=True, index=True),
    )
    
    # Add new fields to season_plan
    op.add_column('season_plan', sa.Column('sku_id', sa.String(100), nullable=True))
    op.add_column('season_plan', sa.Column('planned_units', sa.Integer, nullable=True))
    op.add_column('season_plan', sa.Column('ly_sales', sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column('season_plan', sa.Column('lly_sales', sa.Numeric(precision=18, scale=2), nullable=True))
    
    # Create index on sku_id
    op.create_index('ix_season_plan_sku_id', 'season_plan', ['sku_id'])
    
    # Drop the old unique constraint and create new one including sku_id
    op.drop_constraint('uq_season_plan_composite', 'season_plan', type_='unique')
    op.create_unique_constraint(
        'uq_season_plan_composite',
        'season_plan',
        ['season_id', 'location_id', 'category_id', 'sku_id', 'version']
    )
    
    # Add new fields to locations
    op.add_column('locations', sa.Column('address', sa.String(500), nullable=True))
    op.add_column('locations', sa.Column('city', sa.String(100), nullable=True))
    op.add_column('locations', sa.Column('state', sa.String(100), nullable=True))
    op.add_column('locations', sa.Column('country', sa.String(100), nullable=True))
    op.add_column('locations', sa.Column('postal_code', sa.String(20), nullable=True))
    op.add_column('locations', sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'))


def downgrade() -> None:
    # Remove new fields from locations
    op.drop_column('locations', 'is_active')
    op.drop_column('locations', 'postal_code')
    op.drop_column('locations', 'country')
    op.drop_column('locations', 'state')
    op.drop_column('locations', 'city')
    op.drop_column('locations', 'address')
    
    # Restore old unique constraint
    op.drop_constraint('uq_season_plan_composite', 'season_plan', type_='unique')
    op.create_unique_constraint(
        'uq_season_plan_composite',
        'season_plan',
        ['season_id', 'location_id', 'category_id', 'version']
    )
    
    # Remove index on sku_id
    op.drop_index('ix_season_plan_sku_id', 'season_plan')
    
    # Remove new fields from season_plan
    op.drop_column('season_plan', 'lly_sales')
    op.drop_column('season_plan', 'ly_sales')
    op.drop_column('season_plan', 'planned_units')
    op.drop_column('season_plan', 'sku_id')
    
    # Drop audit_logs table
    op.drop_table('audit_logs')
    
    # Drop audit_action enum
    op.execute('DROP TYPE IF EXISTS audit_action')

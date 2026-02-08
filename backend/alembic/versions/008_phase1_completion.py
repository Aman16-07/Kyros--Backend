"""Phase 1 completion: cluster fields, category hierarchy, user sessions

Revision ID: 008_phase1_completion
Revises: 007_multi_tenant_isolation
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '008_phase1_completion'
down_revision: Union[str, None] = '007_multi_tenant_isolation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cluster fields, category hierarchy fields, and user sessions table."""
    
    # 1. Add new fields to clusters table
    op.add_column('clusters', sa.Column('cluster_code', sa.String(16), nullable=True))
    op.add_column('clusters', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('clusters', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    
    # Generate cluster codes for existing clusters
    # Using substring of UUID to create unique codes
    op.execute("""
        UPDATE clusters 
        SET cluster_code = 'CLU-' || UPPER(SUBSTRING(id::text FROM 1 FOR 8))
        WHERE cluster_code IS NULL
    """)
    
    # Now make cluster_code NOT NULL and add unique constraint
    op.alter_column('clusters', 'cluster_code', nullable=False)
    op.create_unique_constraint('uq_clusters_cluster_code', 'clusters', ['cluster_code'])
    op.create_index('ix_clusters_cluster_code', 'clusters', ['cluster_code'])
    
    # Set is_active to true for existing records
    op.execute("UPDATE clusters SET is_active = true WHERE is_active IS NULL")
    op.alter_column('clusters', 'is_active', nullable=False)
    
    # 2. Add new fields to categories table
    op.add_column('categories', sa.Column('code', sa.String(50), nullable=True))
    op.add_column('categories', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('categories', sa.Column('level', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('categories', sa.Column('path', sa.Text(), nullable=True))
    
    # Create index on parent_id for faster hierarchy queries
    op.create_index('ix_categories_parent_id', 'categories', ['parent_id'])
    op.create_index('ix_categories_path', 'categories', ['path'])
    op.create_unique_constraint('uq_categories_code', 'categories', ['code'])
    op.create_index('ix_categories_code', 'categories', ['code'])
    
    # Set level to 0 for existing categories (they can be updated via API)
    op.execute("UPDATE categories SET level = 0 WHERE level IS NULL")
    op.alter_column('categories', 'level', nullable=False)
    
    # 3. Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('refresh_token_hash', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('browser', sa.String(100), nullable=True),
        sa.Column('os', sa.String(100), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoke_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('ix_user_sessions_is_active', 'user_sessions', ['is_active'])


def downgrade() -> None:
    """Remove cluster fields, category hierarchy fields, and user sessions table."""
    
    # 1. Remove user_sessions table
    op.drop_index('ix_user_sessions_is_active')
    op.drop_index('ix_user_sessions_user_id')
    op.drop_table('user_sessions')
    
    # 2. Remove category fields
    op.drop_index('ix_categories_code')
    op.drop_constraint('uq_categories_code', 'categories', type_='unique')
    op.drop_index('ix_categories_path')
    op.drop_index('ix_categories_parent_id')
    op.drop_column('categories', 'path')
    op.drop_column('categories', 'level')
    op.drop_column('categories', 'description')
    op.drop_column('categories', 'code')
    
    # 3. Remove cluster fields
    op.drop_index('ix_clusters_cluster_code')
    op.drop_constraint('uq_clusters_cluster_code', 'clusters', type_='unique')
    op.drop_column('clusters', 'is_active')
    op.drop_column('clusters', 'description')
    op.drop_column('clusters', 'cluster_code')

"""Add company_id to core models for multi-tenant isolation.

Revision ID: 007_multi_tenant_isolation
Revises: 006_audit_and_fields
Create Date: 2026-02-02

This migration adds company_id foreign key to:
- seasons: Links seasons to a company
- clusters: Links clusters to a company
- locations: Links locations to a company

This enables proper multi-tenancy so users only see their own company's data.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_multi_tenant_isolation'
down_revision = '006_audit_and_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add company_id to seasons
    op.add_column(
        'seasons',
        sa.Column(
            'company_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('companies.id', ondelete='CASCADE'),
            nullable=True,
        )
    )
    op.create_index('ix_seasons_company_id', 'seasons', ['company_id'])
    
    # Add company_id to clusters
    op.add_column(
        'clusters',
        sa.Column(
            'company_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('companies.id', ondelete='CASCADE'),
            nullable=True,
        )
    )
    op.create_index('ix_clusters_company_id', 'clusters', ['company_id'])
    
    # Drop the old unique constraint on clusters.name (global uniqueness)
    op.drop_constraint('clusters_name_key', 'clusters', type_='unique')
    
    # Add company_id to locations
    op.add_column(
        'locations',
        sa.Column(
            'company_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('companies.id', ondelete='CASCADE'),
            nullable=True,
        )
    )
    op.create_index('ix_locations_company_id', 'locations', ['company_id'])


def downgrade() -> None:
    # Remove company_id from locations
    op.drop_index('ix_locations_company_id', 'locations')
    op.drop_column('locations', 'company_id')
    
    # Restore unique constraint on clusters.name
    op.create_unique_constraint('clusters_name_key', 'clusters', ['name'])
    
    # Remove company_id from clusters
    op.drop_index('ix_clusters_company_id', 'clusters')
    op.drop_column('clusters', 'company_id')
    
    # Remove company_id from seasons
    op.drop_index('ix_seasons_company_id', 'seasons')
    op.drop_column('seasons', 'company_id')

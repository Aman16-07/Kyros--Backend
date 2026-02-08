"""Phase 2: OTB positions, adjustments, range architectures

Revision ID: 009_phase2_otb_range
Revises: 008_phase1_completion
Create Date: 2026-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '009_phase2_otb_range'
down_revision: Union[str, None] = '008_phase1_completion'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 2 tables: otb_positions, otb_adjustments, range_architectures."""

    # 1. Create adjustment_status enum
    adjustment_status_enum = postgresql.ENUM(
        'pending', 'approved', 'rejected',
        name='adjustment_status',
        create_type=False,
    )
    adjustment_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create range_status enum
    range_status_enum = postgresql.ENUM(
        'draft', 'submitted', 'under_review', 'approved', 'locked', 'rejected',
        name='range_status',
        create_type=False,
    )
    range_status_enum.create(op.get_bind(), checkfirst=True)

    # 3. Create otb_positions table
    op.create_table(
        'otb_positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('season_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seasons.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('month', sa.Date(), nullable=False),
        sa.Column('planned_otb', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('consumed_otb', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('available_otb', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('last_calculated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('season_id', 'category_id', 'month', name='uq_otb_position_season_category_month'),
    )

    # 4. Create otb_adjustments table
    op.create_table(
        'otb_adjustments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('season_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seasons.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('from_category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('to_category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='adjustment_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. Create range_architectures table
    op.create_table(
        'range_architectures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('season_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seasons.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('price_band', sa.String(50), nullable=True),
        sa.Column('fabric', sa.String(100), nullable=True),
        sa.Column('color_family', sa.String(100), nullable=True),
        sa.Column('style_type', sa.String(20), nullable=True),
        sa.Column('planned_styles', sa.Integer(), nullable=True),
        sa.Column('planned_options', sa.Integer(), nullable=True),
        sa.Column('planned_depth', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'submitted', 'under_review', 'approved', 'locked', 'rejected', name='range_status', create_type=False), nullable=False, server_default='draft'),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_comment', sa.String(1000), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    """Drop Phase 2 tables."""
    op.drop_table('range_architectures')
    op.drop_table('otb_adjustments')
    op.drop_table('otb_positions')

    # Drop enums
    sa.Enum(name='range_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='adjustment_status').drop(op.get_bind(), checkfirst=True)

"""make_company_code_nullable

Revision ID: 003_code_nullable
Revises: 002_company_model
Create Date: 2026-02-01 11:09:36.242680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_code_nullable'
down_revision: Union[str, None] = '002_company_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make company code nullable (code is generated on approval, not on creation)
    op.alter_column('companies', 'code',
               existing_type=sa.VARCHAR(length=8),
               nullable=True)


def downgrade() -> None:
    # Revert - make company code not nullable
    op.alter_column('companies', 'code',
               existing_type=sa.VARCHAR(length=8),
               nullable=False)

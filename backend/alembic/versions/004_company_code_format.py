"""Change company code to XXXX-XXXX format (9 chars)

Revision ID: 004_company_code_format
Revises: 003_code_nullable
Create Date: 2026-02-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_company_code_format'
down_revision: Union[str, None] = '003_code_nullable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change code column from VARCHAR(8) to VARCHAR(9) for XXXX-XXXX format
    op.alter_column('companies', 'code',
                    existing_type=sa.String(8),
                    type_=sa.String(9),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column('companies', 'code',
                    existing_type=sa.String(9),
                    type_=sa.String(8),
                    existing_nullable=True)

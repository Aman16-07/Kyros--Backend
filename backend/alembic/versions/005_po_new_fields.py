"""Add order_date, supplier_name, status to purchase_orders.

Revision ID: 005_po_new_fields
Revises: 004_company_code_format
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_po_new_fields'
down_revision = '004_company_code_format'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create POStatus enum type if it doesn't exist
    # NOTE: Using uppercase values to match SQLAlchemy model enum
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'po_status') THEN
                CREATE TYPE po_status AS ENUM ('DRAFT', 'SUBMITTED', 'CONFIRMED', 'SHIPPED', 'PARTIAL', 'COMPLETE', 'CANCELLED');
            END IF;
        END $$;
    """)
    
    # Add new columns to purchase_orders table if they don't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_orders' AND column_name = 'order_date') THEN
                ALTER TABLE purchase_orders ADD COLUMN order_date DATE;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_orders' AND column_name = 'supplier_name') THEN
                ALTER TABLE purchase_orders ADD COLUMN supplier_name VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_orders' AND column_name = 'status') THEN
                ALTER TABLE purchase_orders ADD COLUMN status po_status DEFAULT 'DRAFT' NOT NULL;
            END IF;
        END $$;
    """)
    
    # Set default value for existing records if any have NULL status
    op.execute("UPDATE purchase_orders SET status = 'DRAFT' WHERE status IS NULL")


def downgrade() -> None:
    # Remove columns
    op.drop_column('purchase_orders', 'status')
    op.drop_column('purchase_orders', 'supplier_name')
    op.drop_column('purchase_orders', 'order_date')
    
    # Drop enum type
    op.execute("DROP TYPE po_status")

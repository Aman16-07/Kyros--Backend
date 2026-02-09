#!/bin/bash
set -e

echo "Starting Kyros Backend..."

# Wait for database to be ready
echo "Waiting for database..."
while ! python -c "import asyncio; from app.core.database import engine; asyncio.run(engine.dispose())" 2>/dev/null; do
    sleep 1
done
echo "Database is ready!"

# Check if this is a fresh database (no alembic_version table)
echo "Checking database state..."
FRESH_DB=$(python -c "
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text(\"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version')\"))
        row = result.scalar()
        print('existing' if row else 'fresh')

asyncio.run(check())
" 2>/dev/null || echo "fresh")

if [ "$FRESH_DB" = "fresh" ]; then
    echo "Fresh database detected. Creating tables from models..."
    python -c "
import asyncio
from app.models.base import Base
from app.core.database import engine

async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create())
"
    echo "Tables created. Stamping alembic to head..."
    alembic stamp head
else
    echo "Existing database. Running migrations..."
    alembic upgrade head
fi

# Seed super admin if not exists
echo "Checking for super admin..."
python -m app.utils.seed_admin

# Start the application
echo "Starting application..."
exec "$@"

#!/bin/bash
set -e

echo "Starting Kyros Backend..."

# Wait for database to be ready
echo "Waiting for database..."
while ! python -c "import asyncio; from app.core.database import engine; asyncio.run(engine.dispose())" 2>/dev/null; do
    sleep 1
done
echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Seed super admin if not exists
echo "Checking for super admin..."
python -m app.utils.seed_admin

# Start the application
echo "Starting application..."
exec "$@"

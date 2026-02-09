# =============================================================================
# Kyros Backend Dockerfile - Multi-stage build
# =============================================================================

# -----------------------------------------------------------------------------
# Base stage - Common dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Development stage
# -----------------------------------------------------------------------------
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    mypy

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8000

# Use entrypoint for migrations and seeding
ENTRYPOINT ["./entrypoint.sh"]

# Development command with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -----------------------------------------------------------------------------
# Production stage
# -----------------------------------------------------------------------------
FROM base AS production

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy application code
COPY --chown=appuser:appgroup . .

# Make entrypoint executable (run as root before switching user)
USER root
RUN chmod +x entrypoint.sh
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use entrypoint for migrations and seeding
ENTRYPOINT ["./entrypoint.sh"]

# Production command with gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]


"""Database engine and session.

This module exposes a synchronous SQLAlchemy engine and session factory
so Alembic autogenerate and sync DB usage work with the standard
`create_engine`/`sessionmaker` APIs.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings


# Use `settings.DB_URL` (env var `DB_URL`).
engine = create_engine(settings.DB_URL, pool_pre_ping=True)

# session factory for sync DB usage
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

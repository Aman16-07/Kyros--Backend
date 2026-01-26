"""Alembic environment configuration for autogenerate.

This file sets `target_metadata` from the project's Base so
`alembic revision --autogenerate` can detect models.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ensure `backend` package is importable when Alembic runs from /backend
HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)

config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
	fileConfig(config.config_file_name)

# Import your project's metadata
from app.models.base import Base  # type: ignore
from app.core.config import settings

target_metadata = Base.metadata

# set sqlalchemy.url from env / settings
if settings.DB_URL:
	config.set_main_option("sqlalchemy.url", settings.DB_URL)


def run_migrations_offline():
	"""Run migrations in 'offline' mode."""
	url = config.get_main_option("sqlalchemy.url")
	context.configure(
		url=url,
		target_metadata=target_metadata,
		literal_binds=True,
		dialect_opts={"paramstyle": "named"},
	)

	with context.begin_transaction():
		context.run_migrations()


def run_migrations_online():
	"""Run migrations in 'online' mode."""
	connectable = engine_from_config(
		config.get_section(config.config_ini_section),
		prefix="sqlalchemy.",
		poolclass=pool.NullPool,
	)

	with connectable.connect() as connection:
		context.configure(connection=connection, target_metadata=target_metadata)

		with context.begin_transaction():
			context.run_migrations()


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()

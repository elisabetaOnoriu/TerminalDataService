from __future__ import annotations
"""
Alembic async environment.

- Builds the async DB URL from .env and a password file (DB_PASS_FILE), so no secrets live in alembic.ini.
- Uses async engine (asyncpg) and bridges to Alembic's sync migration runner via run_sync.
- Imports models so --autogenerate can detect schema changes.
"""
import os
import sys
import asyncio
from logging.config import fileConfig
from pathlib import Path
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.base import Base
from app.models.device_model import Device
from app.models.client_model import Client
from app.models.message_model import Message

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
load_dotenv()

DB_USER = os.getenv("DB_USER", "tds_user")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tds_db")
DB_PASS_FILE = os.getenv("DB_PASS_FILE")

password = ""
if DB_PASS_FILE:
    p = Path(DB_PASS_FILE)
    if not p.exists():
        raise RuntimeError(f"DB_PASS_FILE not found: {p}")
    password = p.read_text().strip()

pwd_part = f":{quote_plus(password)}" if password else ""
DB_ASYNC_URL = f"postgresql+asyncpg://{quote_plus(DB_USER)}{pwd_part}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection)."""
    url = DB_ASYNC_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    """Configure Alembic on a sync connection and run migrations."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode with an async engine."""
    connectable = async_engine_from_config(
        {"sqlalchemy.url": DB_ASYNC_URL},  # pass URL directly; do not rely on alembic.ini
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as async_conn:
        await async_conn.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

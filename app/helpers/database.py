"""Async database session setup and dependency helpers.

This module:
- Loads configuration from environment variables (via dotenv).
- Configures logging for database operations.
- Creates an async SQLAlchemy engine and session factory.
- Exposes `get_db` as a FastAPI dependency to provide an `AsyncSession`.
"""
from logging_config import setup_logging
import os
import logging
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
load_dotenv()


setup_logging()
logger = logging.getLogger(__name__)

DB_USER = os.getenv("DB_USER", "user")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "name")
DB_PASS_FILE = os.getenv("DB_PASS_FILE")

PASSWORD = Path(DB_PASS_FILE).read_text().strip() if DB_PASS_FILE else ""
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

if DATABASE_URL is None:
    raise ValueError("Missing DATABASE_URL in environment")


engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency provider for an asynchronous SQLAlchemy database session.

    It creates an `AsyncSession`, yields it for database operations, and ensures the
    session is properly closed after use, even if an exception occurs.
    """
    logger.info("Creating async DB session")
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Error in get_db: {e}")
            raise
        finally:
            logger.info("Closing async DB session")

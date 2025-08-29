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
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
load_dotenv()


setup_logging()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("Missing DATABASE_URL in environment")


engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """ get db"""
    logger.info("Creating async DB session")
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Error in get_db: {e}")
            raise
        finally:
            logger.info("Closing async DB session")

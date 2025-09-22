import asyncio
import logging

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.helpers.database import get_db
from main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session", autouse=True)
def _quiet_test_logs():
    logging.getLogger().setLevel(logging.WARNING)

    for name in (
        "asyncio",
        "aiosqlite",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "httpx",
        "uvicorn",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
def async_engine():
    engine = create_async_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        echo=False,
    )
    return engine

@pytest.fixture(scope="module", autouse=True)
async def initialized_db(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture()
async def async_session(async_engine):
    async_session_factory = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session
        await session.rollback()

@pytest.fixture()
async def client(async_session: AsyncSession):
    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()

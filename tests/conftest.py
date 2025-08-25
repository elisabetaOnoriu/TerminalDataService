import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.base import Base
from app.helpers.database import get_db
from main import app

from fastapi.testclient import TestClient

"""Create an in-memory SQLite engine for the test session.

  Returns:
      Engine: SQLAlchemy engine connected to an in-memory database.
  """

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine

"""
    Provide a transactional scope around each test function.

    Yields:
        Session: SQLAlchemy session bound to a single transaction.
"""

@pytest.fixture(scope="function")
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


"""
    FastAPI TestClient with database dependency overridden.

    Overrides `get_db` to use the test session, ensuring tests
    run against the in-memory database instead of the real one.

    Yields:
        TestClient: FastAPI test client with isolated DB context.
        
"""
@pytest.fixture()
def client(session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

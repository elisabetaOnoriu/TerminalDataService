import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.base import Base
from sqlalchemy import Table, Column, Integer, String
#
# clients_table = Table(
#     "clients",
#     Base.metadata,
#     Column("client_id", Integer, primary_key=True),
#     Column("name", String)
# )

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    #creezi tabelele
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO clients (client_id, name)
            VALUES (1, 'Test Client')
        """))

    return engine


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

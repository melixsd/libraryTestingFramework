"""
Integration-test-specific conftest.

Provides an autouse db_session fixture so each integration test
gets an isolated transaction against a shared in-memory SQLite database.
The outer connection transaction is rolled back after every test, so data
created by one integration test cannot leak into another test.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import get_db, Base


SQLALCHEMY_TEST_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def db_tables():
    """Create all tables once for the session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def db_session(db_tables):
    """Provide a fresh session per test and override get_db dependency.

    This is autouse for all integration tests.
    """
    from app.main import app

    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    app.dependency_overrides[get_db] = lambda: session
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()

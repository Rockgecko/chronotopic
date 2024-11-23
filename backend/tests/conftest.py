"""Test fixtures for the Chronotopic application."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.base import Base
from main import app
from ingest.base import get_db_session

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture
def test_db(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    
    # Start a transaction
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    # Create a session bound to the connection
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    # Rollback the transaction and close connections
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(test_db):
    """Create a test client."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Don't rollback here, let the test_db fixture handle it
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def sample_event_data():
    """Provide sample event data for testing."""
    return {
        "type": "event",
        "name": "Test Event",
        "begins": 1900,
        "ends": 1901,
        "location": "Test Location",
        "details": "Test Details",
        "stories": ["Test Story"]
    }

@pytest.fixture
def sample_events_data():
    """Provide multiple sample events for testing."""
    return [
        {
            "type": "event",
            "name": "Event 1",
            "begins": -500,
            "ends": -450,
            "location": "Location A",
            "details": "Details 1",
            "stories": ["Story 1"]
        },
        {
            "type": "event",
            "name": "Event 2",
            "begins": 1800,
            "ends": 1850,
            "location": "Location B",
            "details": "Details 2",
            "stories": ["Story 1", "Story 2"]
        },
        {
            "type": "event",
            "name": "Event 3",
            "begins": 1820,
            "ends": 1840,
            "location": "Location A",
            "details": "Details 3",
            "stories": ["Story 2"]
        }
    ]

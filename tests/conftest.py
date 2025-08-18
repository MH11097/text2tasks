import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import get_db_session, Base
from src.config import settings

@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    # Create test database
    test_engine = create_engine(f"sqlite:///{temp_file.name}")
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    yield temp_file.name
    
    # Cleanup
    app.dependency_overrides.clear()
    os.unlink(temp_file.name)

@pytest.fixture
def client(temp_db):
    """Create test client with temporary database"""
    return TestClient(app)

@pytest.fixture
def api_key():
    """Return the test API key"""
    return settings.api_key

@pytest.fixture
def headers(api_key):
    """Return headers with API key"""
    return {"X-API-Key": api_key}
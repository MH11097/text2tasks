import pytest
import asyncio
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.main import app
from src.database import get_db_session, Base, Document, Task, Embedding
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

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session(temp_db):
    """Create a database session for testing"""
    engine = create_engine(f"sqlite:///{temp_db}")
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
async def async_client(temp_db):
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_llm():
    """Mock LLM client for testing"""
    mock = AsyncMock()
    
    # Default mock responses
    mock.extract_summary_and_actions.return_value = {
        "summary": "Test summary",
        "actions": [
            {
                "title": "Test action",
                "owner": "Test User",
                "due": "2024-12-31",
                "blockers": [],
                "project_hint": "Test Project"
            }
        ]
    }
    
    mock.generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    mock.answer_question.return_value = {
        "answer": "Test answer",
        "suggested_next_steps": ["Test step 1", "Test step 2"]
    }
    
    return mock

@pytest.fixture
def sample_document(db_session):
    """Create a sample document for testing"""
    doc = Document(
        text="Sample document content for testing",
        source="meeting",
        source_type="web",
        source_id="test_user_123",
        summary="Sample document summary",
        created_at=datetime.utcnow()
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc

@pytest.fixture
def sample_task(db_session, sample_document):
    """Create a sample task for testing"""
    task = Task(
        title="Sample test task",
        status="new",
        due_date="2025-01-31",
        owner="John Doe",
        blockers=[],
        project_hint="Test Project",
        source_doc_id=sample_document.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task

@pytest.fixture
def sample_embedding(db_session, sample_document):
    """Create a sample embedding for testing"""
    embedding = Embedding(
        document_id=sample_document.id,
        vector=[0.1, 0.2, 0.3, 0.4, 0.5]
    )
    db_session.add(embedding)
    db_session.commit()
    db_session.refresh(embedding)
    return embedding

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch('src.config.settings') as mock:
        mock.openai_api_key = "test-api-key"
        mock.openai_base_url = "https://api.openai.com/v1"
        mock.openai_chat_model = "gpt-4o-mini"
        mock.openai_embedding_model = "text-embedding-3-small"
        mock.api_key = "test-secure-key"
        mock.debug = True
        mock.db_url = "sqlite:///./test.db"
        mock.redis_url = "redis://localhost:6379"
        yield mock
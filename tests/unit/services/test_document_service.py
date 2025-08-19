"""Unit tests for DocumentService"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from src.services.document_service import DocumentService
from src.core.types import SourceType, ProcessingResult
from src.core.exceptions import LLMException, ValidationException
from src.database import Document, Embedding

class TestDocumentService:
    """Test DocumentService functionality"""
    
    @pytest.fixture
    def document_service(self):
        """Create DocumentService instance for testing"""
        return DocumentService()
    
    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client"""
        with patch('src.services.document_service.LLMClient') as mock:
            client = AsyncMock()
            mock.return_value = client
            yield client
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        with patch('src.services.document_service.SessionLocal') as mock:
            session = MagicMock(spec=Session)
            mock.return_value.__aenter__.return_value = session
            mock.return_value.__aexit__.return_value = None
            yield session

class TestProcessDocument:
    """Test process_document functionality"""
    
    @pytest.mark.asyncio
    async def test_process_document_success(self, document_service, mock_llm_client, mock_db_session):
        """Test successful document processing"""
        # Setup mocks
        mock_llm_client.extract_summary_and_actions.return_value = {
            "summary": "Test summary",
            "actions": [
                {"title": "Task 1", "owner": "John", "due": "2025-01-01"},
                {"title": "Task 2", "owner": None, "due": None}
            ]
        }
        mock_llm_client.generate_embeddings.return_value = [0.1, 0.2, 0.3]
        
        # Mock document creation
        mock_doc = MagicMock()
        mock_doc.id = 123
        mock_db_session.add.return_value = None
        mock_db_session.flush = AsyncMock()
        mock_db_session.commit = AsyncMock()
        
        # Test
        with patch('src.services.document_service.Document') as mock_doc_class:
            mock_doc_class.return_value = mock_doc
            
            with patch('src.services.document_service.Embedding') as mock_embedding_class, \
                 patch('src.services.document_service.Task') as mock_task_class:
                
                result = await document_service.process_document(
                    text="Test document content",
                    source="meeting",
                    source_type=SourceType.WEB
                )
        
        # Assertions
        assert result.success is True
        assert result.document_id == 123
        assert result.summary == "Test summary"
        assert result.actions_count == 2
        assert result.error_message is None
        
        # Verify LLM client calls
        mock_llm_client.extract_summary_and_actions.assert_called_once_with("Test document content")
        mock_llm_client.generate_embeddings.assert_called_once_with("Test document content")
    
    @pytest.mark.asyncio
    async def test_process_document_llm_failure(self, document_service, mock_llm_client):
        """Test document processing with LLM failure"""
        # Setup LLM to fail
        mock_llm_client.extract_summary_and_actions.side_effect = Exception("LLM API failed")
        
        # Test
        result = await document_service.process_document(
            text="Test content",
            source="meeting"
        )
        
        # Assertions
        assert result.success is False
        assert result.document_id == 0
        assert result.actions_count == 0
        assert "LLM API failed" in result.error_message
    
    @pytest.mark.asyncio
    async def test_process_document_validation_error(self, document_service):
        """Test document processing with validation error"""
        with patch('src.services.document_service.validate_text_input') as mock_validate:
            mock_validate.side_effect = ValidationException("Invalid text")
            
            result = await document_service.process_document(
                text="",
                source="meeting"
            )
            
            assert result.success is False
            assert "Invalid text" in result.error_message

class TestSearchDocuments:
    """Test search_documents_by_similarity functionality"""
    
    @pytest.mark.asyncio
    async def test_search_documents_success(self, document_service, mock_llm_client, mock_db_session):
        """Test successful document search"""
        # Setup mocks
        mock_llm_client.generate_embeddings.return_value = [0.5, 0.5, 0.5]
        
        # Mock database query results
        mock_docs = [
            (MagicMock(id=1, text="Doc 1", summary="Summary 1", source="meeting", 
                      source_type="web", created_at="2025-01-01"), 
             MagicMock(vector=[0.6, 0.4, 0.5])),
            (MagicMock(id=2, text="Doc 2", summary="Summary 2", source="email",
                      source_type="web", created_at="2025-01-02"), 
             MagicMock(vector=[0.3, 0.7, 0.2]))
        ]
        mock_db_session.query.return_value.join.return_value.all.return_value = mock_docs
        
        # Test
        with patch('src.services.document_service.cosine_similarity') as mock_similarity:
            mock_similarity.side_effect = [0.8, 0.6]  # Similarity scores
            
            results = await document_service.search_documents_by_similarity(
                query="test query",
                top_k=2
            )
        
        # Assertions
        assert len(results) == 2
        assert results[0]["id"] == 1  # Higher similarity first
        assert results[0]["similarity"] == 0.8
        assert results[1]["id"] == 2
        assert results[1]["similarity"] == 0.6
    
    @pytest.mark.asyncio
    async def test_search_documents_empty_results(self, document_service, mock_llm_client, mock_db_session):
        """Test document search with no results"""
        mock_llm_client.generate_embeddings.return_value = [0.1, 0.2, 0.3]
        mock_db_session.query.return_value.join.return_value.all.return_value = []
        
        results = await document_service.search_documents_by_similarity("test query")
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_documents_with_filter(self, document_service, mock_llm_client, mock_db_session):
        """Test document search with source type filter"""
        mock_llm_client.generate_embeddings.return_value = [0.1, 0.2, 0.3]
        mock_query = mock_db_session.query.return_value.join.return_value
        
        await document_service.search_documents_by_similarity(
            "test query", 
            source_type_filter=SourceType.TELEGRAM
        )
        
        # Verify filter was applied
        mock_query.filter.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_documents_embedding_failure(self, document_service, mock_llm_client):
        """Test document search with embedding generation failure"""
        mock_llm_client.generate_embeddings.side_effect = Exception("Embedding failed")
        
        results = await document_service.search_documents_by_similarity("test query")
        
        assert results == []

class TestHelperMethods:
    """Test DocumentService helper methods"""
    
    @pytest.mark.asyncio
    async def test_get_document_by_id(self, document_service, mock_db_session):
        """Test get_document_by_id"""
        mock_doc = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_doc
        
        result = await document_service.get_document_by_id(123)
        
        assert result == mock_doc
        mock_db_session.query.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_get_documents_by_source(self, document_service, mock_db_session):
        """Test get_documents_by_source"""
        mock_docs = [MagicMock(), MagicMock()]
        query_mock = mock_db_session.query.return_value
        query_mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_docs
        
        results = await document_service.get_documents_by_source(
            SourceType.TELEGRAM,
            source_id="user123",
            limit=10
        )
        
        assert results == mock_docs
        # Verify filtering was applied
        assert query_mock.filter.call_count == 2  # source_type and source_id filters
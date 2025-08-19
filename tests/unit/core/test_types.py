"""Unit tests for core types and enums"""

import pytest
from pydantic import ValidationError

from src.core.types import (
    SourceType, DocumentSource, TaskStatus, MessageStatus,
    MessageData, TelegramMessageData, ProcessingResult
)

class TestEnums:
    """Test core enums"""
    
    def test_source_type_enum(self):
        """Test SourceType enum values"""
        assert SourceType.WEB == "web"
        assert SourceType.TELEGRAM == "telegram"
        assert SourceType.EMAIL == "email"
        assert SourceType.API == "api"
    
    def test_document_source_enum(self):
        """Test DocumentSource enum values"""
        assert DocumentSource.EMAIL == "email"
        assert DocumentSource.MEETING == "meeting"
        assert DocumentSource.NOTE == "note"
        assert DocumentSource.OTHER == "other"
        assert DocumentSource.DOCUMENT == "document"
        assert DocumentSource.CHAT == "chat"
    
    def test_task_status_enum(self):
        """Test TaskStatus enum values"""
        assert TaskStatus.NEW == "new"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.BLOCKED == "blocked"
        assert TaskStatus.DONE == "done"
    
    def test_message_status_enum(self):
        """Test MessageStatus enum values"""
        assert MessageStatus.PENDING == "pending"
        assert MessageStatus.PROCESSING == "processing"
        assert MessageStatus.COMPLETED == "completed"
        assert MessageStatus.FAILED == "failed"

class TestMessageData:
    """Test MessageData pydantic model"""
    
    def test_message_data_creation(self):
        """Test basic MessageData creation"""
        data = MessageData(
            text="Test message",
            source_type=SourceType.WEB,
            source_id="test_id",
            metadata={"key": "value"}
        )
        
        assert data.text == "Test message"
        assert data.source_type == SourceType.WEB
        assert data.source_id == "test_id"
        assert data.metadata == {"key": "value"}
    
    def test_message_data_defaults(self):
        """Test MessageData with default values"""
        data = MessageData(
            text="Test message",
            source_type=SourceType.API
        )
        
        assert data.text == "Test message"
        assert data.source_type == SourceType.API
        assert data.source_id is None
        assert data.metadata == {}
    
    def test_message_data_validation(self):
        """Test MessageData validation"""
        # Test missing required fields
        with pytest.raises(ValidationError):
            MessageData()
        
        with pytest.raises(ValidationError):
            MessageData(text="test")  # Missing source_type

class TestTelegramMessageData:
    """Test TelegramMessageData pydantic model"""
    
    def test_telegram_message_data_creation(self):
        """Test TelegramMessageData creation"""
        data = TelegramMessageData(
            text="Hello from Telegram",
            chat_id=12345,
            message_id=67890,
            user_id=54321,
            username="testuser",
            first_name="Test"
        )
        
        assert data.text == "Hello from Telegram"
        assert data.source_type == SourceType.TELEGRAM  # Auto-set
        assert data.chat_id == 12345
        assert data.message_id == 67890
        assert data.user_id == 54321
        assert data.username == "testuser"
        assert data.first_name == "Test"
    
    def test_telegram_message_data_defaults(self):
        """Test TelegramMessageData with optional fields"""
        data = TelegramMessageData(
            text="Test",
            chat_id=123,
            message_id=456,
            user_id=789
        )
        
        assert data.username is None
        assert data.first_name is None
        assert data.source_type == SourceType.TELEGRAM
    
    def test_telegram_message_data_validation(self):
        """Test TelegramMessageData validation"""
        # Test missing required fields
        with pytest.raises(ValidationError):
            TelegramMessageData(text="test")  # Missing chat_id, message_id, user_id
        
        # Test with all required fields
        data = TelegramMessageData(
            text="test",
            chat_id=1,
            message_id=2,
            user_id=3
        )
        assert data.chat_id == 1

class TestProcessingResult:
    """Test ProcessingResult pydantic model"""
    
    def test_processing_result_success(self):
        """Test successful ProcessingResult"""
        result = ProcessingResult(
            document_id=123,
            summary="Test summary",
            actions_count=5,
            success=True
        )
        
        assert result.document_id == 123
        assert result.summary == "Test summary"
        assert result.actions_count == 5
        assert result.success is True
        assert result.error_message is None
    
    def test_processing_result_failure(self):
        """Test failed ProcessingResult"""
        result = ProcessingResult(
            document_id=0,
            summary="",
            actions_count=0,
            success=False,
            error_message="Processing failed"
        )
        
        assert result.document_id == 0
        assert result.summary == ""
        assert result.actions_count == 0
        assert result.success is False
        assert result.error_message == "Processing failed"
    
    def test_processing_result_validation(self):
        """Test ProcessingResult validation"""
        # Test missing required fields
        with pytest.raises(ValidationError):
            ProcessingResult()
        
        # Test with minimal required fields
        result = ProcessingResult(
            document_id=1,
            summary="test",
            actions_count=0,
            success=True
        )
        assert result.error_message is None
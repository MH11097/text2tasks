"""Unit tests for core exceptions"""

import pytest

from src.core.exceptions import (
    BaseWorkOSException, LLMException, ValidationException,
    DocumentNotFoundException, TaskNotFoundException,
    RateLimitException, IntegrationException
)

class TestBaseWorkOSException:
    """Test base exception class"""
    
    def test_base_exception_creation(self):
        """Test basic exception creation"""
        exc = BaseWorkOSException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.error_code is None
    
    def test_base_exception_with_code(self):
        """Test exception with error code"""
        exc = BaseWorkOSException("Test error", error_code="E001")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "E001"
    
    def test_base_exception_inheritance(self):
        """Test that BaseWorkOSException inherits from Exception"""
        exc = BaseWorkOSException("Test")
        assert isinstance(exc, Exception)
        assert isinstance(exc, BaseWorkOSException)

class TestSpecificExceptions:
    """Test specific exception classes"""
    
    def test_llm_exception(self):
        """Test LLMException"""
        exc = LLMException("LLM API failed", "LLM001")
        assert isinstance(exc, BaseWorkOSException)
        assert str(exc) == "LLM API failed"
        assert exc.error_code == "LLM001"
    
    def test_validation_exception(self):
        """Test ValidationException"""
        exc = ValidationException("Invalid input")
        assert isinstance(exc, BaseWorkOSException)
        assert str(exc) == "Invalid input"
    
    def test_document_not_found_exception(self):
        """Test DocumentNotFoundException"""
        exc = DocumentNotFoundException("Document 123 not found")
        assert isinstance(exc, BaseWorkOSException)
        assert str(exc) == "Document 123 not found"
    
    def test_task_not_found_exception(self):
        """Test TaskNotFoundException"""
        exc = TaskNotFoundException("Task 456 not found")
        assert isinstance(exc, BaseWorkOSException)
        assert str(exc) == "Task 456 not found"
    
    def test_rate_limit_exception(self):
        """Test RateLimitException"""
        exc = RateLimitException("Rate limit exceeded")
        assert isinstance(exc, BaseWorkOSException)
        assert str(exc) == "Rate limit exceeded"
    
    def test_integration_exception(self):
        """Test IntegrationException"""
        exc = IntegrationException("Telegram API failed")
        assert isinstance(exc, BaseWorkOSException)
        assert str(exc) == "Telegram API failed"

class TestExceptionBehavior:
    """Test exception behavior and usage"""
    
    def test_exception_raising_and_catching(self):
        """Test raising and catching custom exceptions"""
        with pytest.raises(ValidationException):
            raise ValidationException("Test validation error")
        
        with pytest.raises(BaseWorkOSException):
            raise LLMException("Test LLM error")
    
    def test_exception_chaining(self):
        """Test exception chaining"""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            exc = LLMException("LLM processing failed") from e
            assert exc.__cause__ is e
    
    def test_exception_with_context(self):
        """Test exceptions with additional context"""
        exc = DocumentNotFoundException(
            "Document not found", 
            error_code="DOC404"
        )
        
        # Test that we can access both message and error_code
        assert str(exc) == "Document not found"
        assert exc.error_code == "DOC404"
        assert hasattr(exc, 'message')
        assert exc.message == "Document not found"
"""Unit tests for security functions"""

import pytest
from fastapi import HTTPException

from src.security import (
    validate_text_input, validate_source_input, validate_task_status,
    validate_owner_input, validate_date_input, validate_question_input,
    validate_api_key_header, InputValidationError
)

class TestValidateTextInput:
    """Test validate_text_input function"""
    
    def test_valid_text(self):
        """Test validation of valid text"""
        result = validate_text_input("This is valid text", field_name="content")
        assert result == "This is valid text"
    
    def test_text_with_html_escaping(self):
        """Test text with HTML characters gets escaped"""
        result = validate_text_input("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
    
    def test_text_too_long(self):
        """Test text exceeding max length"""
        long_text = "a" * 50001
        with pytest.raises(InputValidationError) as exc_info:
            validate_text_input(long_text)
        assert "exceeds maximum length" in str(exc_info.value)
    
    def test_text_with_null_bytes(self):
        """Test text containing null bytes"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_text_input("text with \x00 null byte")
        assert "contains null bytes" in str(exc_info.value)
    
    def test_non_string_input(self):
        """Test non-string input"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_text_input(123)
        assert "must be a string" in str(exc_info.value)
    
    def test_custom_max_length(self):
        """Test custom max length"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_text_input("This text is too long", max_length=10)
        assert "exceeds maximum length of 10" in str(exc_info.value)
    
    def test_custom_field_name(self):
        """Test custom field name in error"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_text_input(123, field_name="description")
        assert "description must be a string" in str(exc_info.value)

class TestValidateSourceInput:
    """Test validate_source_input function"""
    
    def test_valid_sources(self):
        """Test all valid source types"""
        valid_sources = ["email", "meeting", "note", "other", "document", "chat"]
        for source in valid_sources:
            result = validate_source_input(source)
            assert result == source
    
    def test_invalid_source(self):
        """Test invalid source type"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_source_input("invalid_source")
        assert "source must be one of" in str(exc_info.value)
    
    def test_non_string_source(self):
        """Test non-string source"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_source_input(123)
        assert "source must be a string" in str(exc_info.value)

class TestValidateTaskStatus:
    """Test validate_task_status function"""
    
    def test_valid_statuses(self):
        """Test all valid task statuses"""
        valid_statuses = ["new", "in_progress", "blocked", "done"]
        for status in valid_statuses:
            result = validate_task_status(status)
            assert result == status
    
    def test_invalid_status(self):
        """Test invalid task status"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_task_status("invalid_status")
        assert "status must be one of" in str(exc_info.value)
    
    def test_non_string_status(self):
        """Test non-string status"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_task_status(123)
        assert "status must be a string" in str(exc_info.value)

class TestValidateOwnerInput:
    """Test validate_owner_input function"""
    
    def test_valid_owner(self):
        """Test valid owner name"""
        result = validate_owner_input("John Doe")
        assert result == "John Doe"
    
    def test_owner_none(self):
        """Test None owner (should be allowed)"""
        result = validate_owner_input(None)
        assert result is None
    
    def test_owner_too_long(self):
        """Test owner name too long"""
        long_name = "a" * 101
        with pytest.raises(InputValidationError) as exc_info:
            validate_owner_input(long_name)
        assert "exceeds maximum length of 100" in str(exc_info.value)
    
    def test_owner_with_invalid_characters(self):
        """Test owner with invalid characters"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_owner_input("John<script>")
        assert "contains invalid characters" in str(exc_info.value)
    
    def test_owner_whitespace_stripped(self):
        """Test that whitespace is stripped"""
        result = validate_owner_input("  John Doe  ")
        assert result == "John Doe"
    
    def test_non_string_owner(self):
        """Test non-string owner"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_owner_input(123)
        assert "owner must be a string" in str(exc_info.value)

class TestValidateDateInput:
    """Test validate_date_input function"""
    
    def test_valid_date(self):
        """Test valid date format"""
        result = validate_date_input("2025-01-15")
        assert result == "2025-01-15"
    
    def test_date_none(self):
        """Test None date (should be allowed)"""
        result = validate_date_input(None)
        assert result is None
    
    def test_invalid_date_format(self):
        """Test invalid date format"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_date_input("2025/01/15")
        assert "must be in YYYY-MM-DD format" in str(exc_info.value)
    
    def test_invalid_month(self):
        """Test invalid month"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_date_input("2025-13-01")
        assert "Invalid month" in str(exc_info.value)
    
    def test_invalid_day(self):
        """Test invalid day"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_date_input("2025-01-32")
        assert "Invalid day" in str(exc_info.value)
    
    def test_year_out_of_range(self):
        """Test year out of valid range"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_date_input("2019-01-01")
        assert "Year must be between 2020 and 2030" in str(exc_info.value)
    
    def test_non_string_date(self):
        """Test non-string date"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_date_input(20250115)
        assert "date must be a string" in str(exc_info.value)

class TestValidateQuestionInput:
    """Test validate_question_input function"""
    
    def test_valid_question(self):
        """Test valid question"""
        result = validate_question_input("What is the status of project X?")
        assert result == "What is the status of project X?"
    
    def test_question_too_long(self):
        """Test question too long"""
        long_question = "a" * 1001
        with pytest.raises(InputValidationError) as exc_info:
            validate_question_input(long_question)
        assert "exceeds maximum length of 1000" in str(exc_info.value)
    
    def test_question_too_short(self):
        """Test question too short"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_question_input("hi")
        assert "must be at least 3 characters" in str(exc_info.value)
    
    def test_question_whitespace_stripped(self):
        """Test that whitespace is stripped"""
        result = validate_question_input("  What is this?  ")
        assert result == "What is this?"
    
    def test_question_html_escaped(self):
        """Test HTML escaping in question"""
        result = validate_question_input("What about <script> tags?")
        assert "&lt;script&gt;" in result
    
    def test_non_string_question(self):
        """Test non-string question"""
        with pytest.raises(InputValidationError) as exc_info:
            validate_question_input(123)
        assert "question must be a string" in str(exc_info.value)

class TestValidateApiKeyHeader:
    """Test validate_api_key_header function"""
    
    def test_valid_api_key(self):
        """Test valid API key"""
        result = validate_api_key_header("sk-1234567890abcdef")
        assert result == "sk-1234567890abcdef"
    
    def test_missing_api_key(self):
        """Test missing API key"""
        with pytest.raises(HTTPException) as exc_info:
            validate_api_key_header(None)
        assert exc_info.value.status_code == 401
        assert "Missing API key" in str(exc_info.value.detail)
    
    def test_empty_api_key(self):
        """Test empty API key"""
        with pytest.raises(HTTPException) as exc_info:
            validate_api_key_header("")
        assert exc_info.value.status_code == 401
        assert "Missing API key" in str(exc_info.value.detail)
    
    def test_api_key_too_short(self):
        """Test API key too short"""
        with pytest.raises(HTTPException) as exc_info:
            validate_api_key_header("short")
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value.detail)
    
    def test_api_key_suspicious_characters(self):
        """Test API key with suspicious characters"""
        with pytest.raises(HTTPException) as exc_info:
            validate_api_key_header("sk-1234<script>alert('xss')</script>")
        assert exc_info.value.status_code == 401
        assert "Invalid API key format" in str(exc_info.value.detail)
    
    def test_non_string_api_key(self):
        """Test non-string API key"""
        with pytest.raises(HTTPException) as exc_info:
            validate_api_key_header(123)
        assert exc_info.value.status_code == 401
        assert "Invalid API key format" in str(exc_info.value.detail)

class TestInputValidationError:
    """Test InputValidationError exception"""
    
    def test_input_validation_error_creation(self):
        """Test creating InputValidationError"""
        error = InputValidationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_input_validation_error_inheritance(self):
        """Test InputValidationError inheritance"""
        error = InputValidationError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, InputValidationError)
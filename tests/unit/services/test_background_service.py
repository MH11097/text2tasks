"""Unit tests for BackgroundService"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.background_service import BackgroundService, process_message_async, cleanup_old_tasks, send_notification
from src.core.types import MessageData, SourceType, ProcessingResult
from src.core.exceptions import IntegrationException

class TestBackgroundService:
    """Test BackgroundService functionality"""
    
    @pytest.fixture
    def background_service(self):
        """Create BackgroundService instance for testing"""
        return BackgroundService()

class TestQueueMessageProcessing:
    """Test queue_message_processing functionality"""
    
    @pytest.mark.asyncio
    async def test_queue_message_processing_normal_priority(self, background_service):
        """Test queueing message with normal priority"""
        message_data = MessageData(
            text="Test message",
            source_type=SourceType.WEB,
            source_id="test_user"
        )
        
        with patch('src.services.background_service.process_message_async') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "task_123"
            mock_task.apply_async.return_value = mock_result
            
            task_id = await background_service.queue_message_processing(
                message_data, 
                priority="normal"
            )
        
        assert task_id == "task_123"
        mock_task.apply_async.assert_called_once_with(
            args=[message_data.dict()],
            priority=5
        )
    
    @pytest.mark.asyncio
    async def test_queue_message_processing_high_priority(self, background_service):
        """Test queueing message with high priority"""
        message_data = MessageData(
            text="Urgent message",
            source_type=SourceType.TELEGRAM,
            source_id="urgent_user"
        )
        
        with patch('src.services.background_service.process_message_async') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "task_456"
            mock_task.apply_async.return_value = mock_result
            
            task_id = await background_service.queue_message_processing(
                message_data, 
                priority="high"
            )
        
        assert task_id == "task_456"
        mock_task.apply_async.assert_called_once_with(
            args=[message_data.dict()],
            priority=9
        )
    
    @pytest.mark.asyncio
    async def test_queue_message_processing_failure(self, background_service):
        """Test queueing message failure"""
        message_data = MessageData(
            text="Test message",
            source_type=SourceType.WEB
        )
        
        with patch('src.services.background_service.process_message_async') as mock_task:
            mock_task.apply_async.side_effect = Exception("Queue failed")
            
            with pytest.raises(IntegrationException) as exc_info:
                await background_service.queue_message_processing(message_data)
            
            assert "Queueing failed" in str(exc_info.value)

class TestGetTaskStatus:
    """Test get_task_status functionality"""
    
    @pytest.mark.asyncio
    async def test_get_task_status_successful(self, background_service):
        """Test getting status of successful task"""
        with patch('src.services.background_service.celery_app.AsyncResult') as mock_result:
            mock_task = MagicMock()
            mock_task.status = "SUCCESS"
            mock_task.result = {"document_id": 123, "success": True}
            mock_task.successful.return_value = True
            mock_task.failed.return_value = False
            mock_result.return_value = mock_task
            
            status = await background_service.get_task_status("task_123")
        
        assert status["task_id"] == "task_123"
        assert status["status"] == "SUCCESS"
        assert status["result"] == {"document_id": 123, "success": True}
        assert status["error"] is None
    
    @pytest.mark.asyncio
    async def test_get_task_status_failed(self, background_service):
        """Test getting status of failed task"""
        with patch('src.services.background_service.celery_app.AsyncResult') as mock_result:
            mock_task = MagicMock()
            mock_task.status = "FAILURE"
            mock_task.result = Exception("Task failed")
            mock_task.successful.return_value = False
            mock_task.failed.return_value = True
            mock_result.return_value = mock_task
            
            status = await background_service.get_task_status("task_456")
        
        assert status["task_id"] == "task_456"
        assert status["status"] == "FAILURE"
        assert status["result"] is None
        assert "Task failed" in status["error"]
    
    @pytest.mark.asyncio
    async def test_get_task_status_in_progress(self, background_service):
        """Test getting status of in-progress task"""
        with patch('src.services.background_service.celery_app.AsyncResult') as mock_result:
            mock_task = MagicMock()
            mock_task.status = "PROGRESS"
            mock_task.info = {"step": "processing", "progress": 50}
            mock_task.successful.return_value = False
            mock_task.failed.return_value = False
            mock_result.return_value = mock_task
            
            status = await background_service.get_task_status("task_789")
        
        assert status["task_id"] == "task_789"
        assert status["status"] == "PROGRESS"
        assert status["progress"] == {"step": "processing", "progress": 50}
    
    @pytest.mark.asyncio
    async def test_get_task_status_exception(self, background_service):
        """Test getting task status when exception occurs"""
        with patch('src.services.background_service.celery_app.AsyncResult') as mock_result:
            mock_result.side_effect = Exception("Redis connection failed")
            
            status = await background_service.get_task_status("task_error")
        
        assert status["task_id"] == "task_error"
        assert status["status"] == "UNKNOWN"
        assert "Redis connection failed" in status["error"]

class TestCeleryTasks:
    """Test Celery task functions"""

    @pytest.mark.asyncio 
    async def test_process_message_async_success(self):
        """Test successful message processing task"""
        message_data_dict = {
            "text": "Test message for processing",
            "source_type": "telegram",
            "source_id": "user_123",
            "metadata": {"chat_id": 456}
        }
        
        # Mock the task context
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3
        
        with patch('src.services.background_service.DocumentService') as mock_doc_service_class:
            mock_doc_service = AsyncMock()
            mock_doc_service.process_document.return_value = ProcessingResult(
                document_id=123,
                summary="Test summary",
                actions_count=2,
                success=True
            )
            mock_doc_service_class.return_value = mock_doc_service
            
            with patch('src.services.background_service.MessageData') as mock_message_data:
                mock_message_data.return_value = MagicMock(
                    text="Test message for processing",
                    source_type=SourceType.TELEGRAM,
                    source_id="user_123",
                    metadata={"chat_id": 456}
                )
                
                # Call the task function directly
                result = await process_message_async.__wrapped__(mock_task, message_data_dict)
        
        # Assertions
        assert result["success"] is True
        assert result["document_id"] == 123
        assert result["summary"] == "Test summary"
        assert result["actions_count"] == 2
        assert "processed_at" in result
        
        # Verify progress updates were called
        assert mock_task.update_state.call_count >= 2
    
    def test_cleanup_old_tasks(self):
        """Test cleanup old tasks function"""
        result = cleanup_old_tasks()
        
        # Should return success even if actual cleanup logic isn't implemented
        assert result["success"] is True
        assert "cleaned_count" in result
        assert "cutoff_time" in result
    
    def test_send_notification_success(self):
        """Test successful notification sending"""
        result = send_notification(
            recipient="user@example.com",
            message="Test notification",
            notification_type="info"
        )
        
        assert result["success"] is True
        assert result["recipient"] == "user@example.com"
        assert result["type"] == "info"
        assert "sent_at" in result
    
    def test_send_notification_failure(self):
        """Test notification sending failure"""
        with patch('src.services.background_service.logger') as mock_logger:
            # Force an exception in the notification logic
            with patch('src.services.background_service.datetime') as mock_datetime:
                mock_datetime.utcnow.side_effect = Exception("Time error")
                
                result = send_notification(
                    recipient="user@example.com",
                    message="Test notification"
                )
        
        assert result["success"] is False
        assert "error" in result

class TestCeleryTaskRetry:
    """Test Celery task retry functionality"""
    
    @pytest.mark.asyncio
    async def test_process_message_async_retry(self):
        """Test message processing with retry"""
        message_data_dict = {
            "text": "Test message",
            "source_type": "web",
            "source_id": None,
            "metadata": {}
        }
        
        # Mock task that will retry
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()
        mock_task.request.retries = 1
        mock_task.max_retries = 3
        mock_task.retry = MagicMock(side_effect=Exception("Retry called"))
        
        with patch('src.services.background_service.DocumentService') as mock_doc_service_class:
            mock_doc_service = AsyncMock()
            mock_doc_service.process_document.side_effect = Exception("Temporary failure")
            mock_doc_service_class.return_value = mock_doc_service
            
            with patch('src.services.background_service.MessageData'):
                with pytest.raises(Exception) as exc_info:
                    await process_message_async.__wrapped__(mock_task, message_data_dict)
                
                # Should call retry
                assert "Retry called" in str(exc_info.value)
                mock_task.retry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_async_max_retries_exceeded(self):
        """Test message processing when max retries exceeded"""
        message_data_dict = {
            "text": "Test message",
            "source_type": "web",
            "source_id": None,
            "metadata": {}
        }
        
        # Mock task that has exceeded max retries
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()
        mock_task.request.retries = 3
        mock_task.max_retries = 3
        
        with patch('src.services.background_service.DocumentService') as mock_doc_service_class:
            mock_doc_service = AsyncMock()
            mock_doc_service.process_document.side_effect = Exception("Persistent failure")
            mock_doc_service_class.return_value = mock_doc_service
            
            with patch('src.services.background_service.MessageData'):
                result = await process_message_async.__wrapped__(mock_task, message_data_dict)
        
        # Should return failure result instead of retrying
        assert result["success"] is False
        assert "Persistent failure" in result["error"]
        assert "failed_at" in result
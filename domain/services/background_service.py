"""Background task processing service với Celery"""

from celery import Celery
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..config import settings
from ..core.types import MessageData, ProcessingResult, SourceType
from ..core.exceptions import IntegrationException
from .document_service import DocumentService

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'ai-work-os',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['src.services.background_service']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'src.services.background_service.process_message_async': {'queue': 'high'},
        'src.services.background_service.cleanup_old_tasks': {'queue': 'low'},
    },
    beat_schedule={
        'cleanup-old-completed-tasks': {
            'task': 'src.services.background_service.cleanup_old_tasks',
            'schedule': 3600.0,  # Every hour
        },
    }
)

class BackgroundService:
    """
    Service để handle background tasks
    Separation of Concerns: Async processing logic
    """
    
    def __init__(self):
        self.document_service = DocumentService()
    
    async def queue_message_processing(
        self, 
        message_data: MessageData,
        priority: str = "normal"
    ) -> str:
        """
        Queue message for background processing
        Returns task ID
        """
        try:
            # Queue task với priority
            if priority == "high":
                task = process_message_async.apply_async(
                    args=[message_data.dict()],
                    priority=9
                )
            else:
                task = process_message_async.apply_async(
                    args=[message_data.dict()],
                    priority=5
                )
            
            logger.info(
                "Message queued for processing",
                extra={
                    "task_id": task.id,
                    "source_type": message_data.source_type,
                    "priority": priority
                }
            )
            
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to queue message processing: {e}")
            raise IntegrationException(f"Queueing failed: {e}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status của background task"""
        try:
            task = celery_app.AsyncResult(task_id)
            
            return {
                "task_id": task_id,
                "status": task.status,
                "result": task.result if task.successful() else None,
                "error": str(task.result) if task.failed() else None,
                "progress": task.info if task.status == 'PROGRESS' else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {
                "task_id": task_id,
                "status": "UNKNOWN",
                "error": str(e)
            }

# Celery tasks
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_message_async(self, message_data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process message asynchronously
    DRY: Reuse document processing logic
    """
    try:
        # Update task progress
        self.update_state(state='PROGRESS', meta={'step': 'initializing'})
        
        # Create MessageData object
        message_data = MessageData(**message_data_dict)
        
        # Process document
        self.update_state(state='PROGRESS', meta={'step': 'processing_document'})
        
        document_service = DocumentService()
        result = await document_service.process_document(
            text=message_data.text,
            source="chat",
            source_type=message_data.source_type,
            source_id=message_data.source_id,
            metadata=message_data.metadata
        )
        
        if result.success:
            logger.info(
                "Message processed successfully in background",
                extra={
                    "document_id": result.document_id,
                    "actions_count": result.actions_count,
                    "source_type": message_data.source_type
                }
            )
            
            return {
                "success": True,
                "document_id": result.document_id,
                "summary": result.summary,
                "actions_count": result.actions_count,
                "processed_at": datetime.utcnow().isoformat()
            }
        else:
            raise Exception(f"Document processing failed: {result.error_message}")
            
    except Exception as e:
        logger.error(f"Background message processing failed: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        # Final failure
        return {
            "success": False,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }

@celery_app.task
def cleanup_old_tasks() -> Dict[str, Any]:
    """
    Cleanup old completed tasks from Celery backend
    """
    try:
        # Get all task results older than 24 hours
        from celery.result import AsyncResult
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        cleaned_count = 0
        
        # This would need implementation based on your Redis setup
        # For now, just log the cleanup attempt
        logger.info("Old task cleanup initiated")
        
        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "cutoff_time": cutoff_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Task cleanup failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@celery_app.task
def send_notification(
    recipient: str,
    message: str, 
    notification_type: str = "info"
) -> Dict[str, Any]:
    """
    Send notification (placeholder for future notification system)
    """
    try:
        logger.info(
            f"Notification queued: {notification_type}",
            extra={
                "recipient": recipient,
                "message_preview": message[:50]
            }
        )
        
        # Placeholder - implement actual notification logic
        # Could be email, SMS, push notification, etc.
        
        return {
            "success": True,
            "sent_at": datetime.utcnow().isoformat(),
            "recipient": recipient,
            "type": notification_type
        }
        
    except Exception as e:
        logger.error(f"Notification sending failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
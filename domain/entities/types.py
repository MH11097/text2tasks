"""Common types and enums for domain layer"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class SourceType(str, Enum):
    WEB = "web"
    TELEGRAM = "telegram" 
    EMAIL = "email"
    API = "api"

class DocumentSource(str, Enum):
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    OTHER = "other"
    DOCUMENT = "document"
    CHAT = "chat"

class TaskStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class MessageStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MessageData(BaseModel):
    """Base message data structure"""
    text: str
    source_type: SourceType
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class TelegramMessageData(MessageData):
    """Telegram-specific message data"""
    source_type: SourceType = SourceType.TELEGRAM
    chat_id: int
    message_id: int
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    
class ProcessingResult(BaseModel):
    """Result of document processing"""
    document_id: int
    summary: str
    actions_count: int
    success: bool
    error_message: Optional[str] = None
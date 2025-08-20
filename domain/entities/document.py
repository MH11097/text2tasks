"""Document domain entity"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class DocumentEntity(BaseModel):
    """Domain entity representing a document"""
    id: Optional[int] = None
    text: str
    source: str  # email|meeting|note|other|document|chat
    source_type: str  # web|telegram|email|api
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    summary: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
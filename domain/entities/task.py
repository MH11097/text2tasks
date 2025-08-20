"""Task domain entity"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class TaskEntity(BaseModel):
    """Domain entity representing a task"""
    id: Optional[int] = None
    title: str
    status: str = "new"  # new|in_progress|blocked|done
    due_date: Optional[str] = None  # YYYY-MM-DD format
    owner: Optional[str] = None
    blockers: List[str] = []
    project_hint: Optional[str] = None
    source_doc_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
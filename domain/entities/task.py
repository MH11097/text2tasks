"""Task domain entity"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class TaskEntity(BaseModel):
    """Domain entity representing a task"""
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str = "new"  # new|in_progress|blocked|done
    priority: str = "medium"  # low|medium|high|urgent
    due_date: Optional[str] = None  # YYYY-MM-DD format
    owner: Optional[str] = None
    blockers: List[str] = []
    project_hint: Optional[str] = None
    source_doc_id: Optional[int] = None  # Made optional for manually created tasks
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    linked_document_ids: List[int] = []  # IDs of linked documents
    
    class Config:
        from_attributes = True
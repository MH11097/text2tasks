from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class IngestRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Text content to process")
    source: str = Field(..., pattern="^(email|meeting|note|other|document|chat)$", description="Source type of the document")
    
    @validator('text')
    def validate_text_content(cls, v):
        from .security import validate_text_input
        return validate_text_input(v, max_length=50000, field_name="text")
    
    @validator('source')
    def validate_source_type(cls, v):
        from .security import validate_source_input
        return validate_source_input(v)

class ActionItem(BaseModel):
    title: str
    owner: Optional[str] = None
    due: Optional[str] = Field(None, pattern="^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    blockers: List[str] = []
    project_hint: Optional[str] = None

class IngestResponse(BaseModel):
    document_id: str
    summary: str
    actions: List[ActionItem]

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000, description="Question to ask")
    top_k: int = Field(6, ge=1, le=12, description="Number of documents to retrieve")
    
    @validator('question')
    def validate_question_content(cls, v):
        from .security import validate_question_input
        return validate_question_input(v)

class AskResponse(BaseModel):
    answer: str
    refs: List[str]
    suggested_next_steps: List[str]

class TaskBase(BaseModel):
    title: str
    status: str = Field("new", pattern="^(new|in_progress|blocked|done)$")
    due_date: Optional[str] = Field(None, pattern="^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    owner: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    status: str
    due_date: Optional[str]
    owner: Optional[str]
    source_doc_id: Optional[str]  # Made optional for manually created tasks

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    priority: Optional[str] = Field("medium", pattern="^(low|medium|high|urgent)$", description="Task priority")
    due_date: Optional[str] = Field(None, pattern="^[0-9]{4}-[0-9]{2}-[0-9]{2}$", description="Due date in YYYY-MM-DD format")
    owner: Optional[str] = Field(None, max_length=100, description="Task owner")
    document_ids: List[int] = Field(default_factory=list, description="List of document IDs to link to this task")
    created_by: Optional[str] = Field(None, max_length=100, description="Who created the task")
    
    @validator('title')
    def validate_title_content(cls, v):
        from infrastructure.security.security import validate_text_input
        return validate_text_input(v, max_length=255, field_name="title")
    
    @validator('description')
    def validate_description_content(cls, v):
        if v is not None:
            from infrastructure.security.security import validate_text_input
            return validate_text_input(v, max_length=2000, field_name="description")
        return v
    
    @validator('priority')
    def validate_priority_value(cls, v):
        if v is not None:
            valid_priorities = ["low", "medium", "high", "urgent"]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v
    
    @validator('owner')
    def validate_owner_value(cls, v):
        if v is not None:
            from infrastructure.security.security import validate_owner_input
            return validate_owner_input(v)
        return v
    
    @validator('due_date')
    def validate_due_date_value(cls, v):
        if v is not None:
            from infrastructure.security.security import validate_date_input
            return validate_date_input(v)
        return v

class TaskUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(new|in_progress|blocked|done)$", description="Task status")
    owner: Optional[str] = Field(None, max_length=100, description="Task owner")
    due_date: Optional[str] = Field(None, pattern="^[0-9]{4}-[0-9]{2}-[0-9]{2}$", description="Due date in YYYY-MM-DD format")
    
    @validator('status')
    def validate_status_value(cls, v):
        if v is not None:
            from infrastructure.security.security import validate_task_status
            return validate_task_status(v)
        return v
    
    @validator('owner')
    def validate_owner_value(cls, v):
        if v is not None:
            from infrastructure.security.security import validate_owner_input
            return validate_owner_input(v)
        return v
    
    @validator('due_date')
    def validate_due_date_value(cls, v):
        if v is not None:
            from infrastructure.security.security import validate_date_input
            return validate_date_input(v)
        return v

class StatusCounts(BaseModel):
    new: int
    in_progress: int
    blocked: int
    done: int

class StatusResponse(BaseModel):
    summary: str
    counts: StatusCounts
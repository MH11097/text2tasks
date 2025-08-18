from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class IngestRequest(BaseModel):
    text: str
    source: str = Field(..., regex="^(email|meeting|note|other)$")

class ActionItem(BaseModel):
    title: str
    owner: Optional[str] = None
    due: Optional[str] = Field(None, regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    blockers: List[str] = []
    project_hint: Optional[str] = None

class IngestResponse(BaseModel):
    document_id: str
    summary: str
    actions: List[ActionItem]

class AskRequest(BaseModel):
    question: str
    top_k: int = Field(6, ge=1, le=12)

class AskResponse(BaseModel):
    answer: str
    refs: List[str]
    suggested_next_steps: List[str]

class TaskBase(BaseModel):
    title: str
    status: str = Field("new", regex="^(new|in_progress|blocked|done)$")
    due_date: Optional[str] = Field(None, regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    owner: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    status: str
    due_date: Optional[str]
    owner: Optional[str]
    source_doc_id: str

class TaskUpdate(BaseModel):
    status: Optional[str] = Field(None, regex="^(new|in_progress|blocked|done)$")
    owner: Optional[str] = None
    due_date: Optional[str] = Field(None, regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

class StatusCounts(BaseModel):
    new: int
    in_progress: int
    blocked: int
    done: int

class StatusResponse(BaseModel):
    summary: str
    counts: StatusCounts
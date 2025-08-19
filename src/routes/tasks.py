from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db_session, Task
from ..schemas import TaskResponse, TaskUpdate
from ..config import settings

router = APIRouter()

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    from ..security import validate_api_key_header
    validated_key = validate_api_key_header(x_api_key)
    if validated_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return validated_key

def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validate task status transitions according to state machine rules"""
    valid_transitions = {
        "new": ["in_progress", "blocked"],
        "in_progress": ["done", "blocked"],
        "blocked": ["in_progress"],
        "done": []  # No transitions from done
    }
    
    if current_status == new_status:
        return True
    
    return new_status in valid_transitions.get(current_status, [])

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None, regex="^(new|in_progress|blocked|done)$"),
    owner: Optional[str] = Query(None),
    db: Session = Depends(get_db_session)
):
    """List tasks with optional filtering by status and owner"""
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    
    if owner:
        query = query.filter(Task.owner == owner)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    return [
        TaskResponse(
            id=str(task.id),
            title=task.title,
            status=task.status,
            due_date=task.due_date,
            owner=task.owner,
            source_doc_id=str(task.source_doc_id)
        )
        for task in tasks
    ]

@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    """Update task status, owner, or due date"""
    
    # Find the task
    task = db.query(Task).filter(Task.id == int(task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Validate status transition if status is being updated
    if task_update.status and task_update.status != task.status:
        if not validate_status_transition(task.status, task_update.status):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status transition from {task.status} to {task_update.status}"
            )
        task.status = task_update.status
    
    # Update other fields
    if task_update.owner is not None:
        task.owner = task_update.owner
    
    if task_update.due_date is not None:
        task.due_date = task_update.due_date
    
    try:
        db.commit()
        return {"message": "Task updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import Optional, List

from ..schemas.schemas import TaskResponse, TaskUpdate
from domain.services.task_service import TaskService
from domain.entities.types import TaskStatus
from domain.entities.exceptions import TaskNotFoundException, ValidationException
from shared.config.settings import settings
import logging
from app.dependencies import container

router = APIRouter()
task_service = TaskService(
    task_repository=container.task_repository
)
logger = logging.getLogger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    from infrastructure.security.security import validate_api_key_header
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
    owner: Optional[str] = Query(None)
):
    """
    List tasks using service layer - DRY refactored
    """
    try:
        # Parse status to enum if provided
        status_filter = None
        if status:
            status_filter = TaskStatus(status)
        
        # Get tasks using service layer
        tasks = task_service.get_tasks(
            status_filter=status_filter,
            owner_filter=owner,
            limit=200
        )
        
        # Convert to response format
        response_tasks = []
        for task in tasks:
            response_tasks.append(TaskResponse(
                id=task["id"],
                title=task["title"],
                status=task["status"],
                due_date=task["due_date"],
                owner=task["owner"],
                source_doc_id=task["source_doc_id"]
            ))
        
        logger.info(
            "Tasks listed successfully",
            extra={
                "count": len(response_tasks),
                "status_filter": status,
                "owner_filter": owner
            }
        )
        
        return response_tasks
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    api_key: str = Depends(verify_api_key)
):
    """
    Update task using service layer - DRY refactored
    """
    try:
        # Convert task_id to int
        task_id_int = int(task_id)
        
        # Update task using service layer
        updated_task = task_service.update_task(
            task_id=task_id_int,
            status=task_update.status,
            owner=task_update.owner,
            due_date=task_update.due_date
        )
        
        logger.info(
            "Task updated successfully",
            extra={
                "task_id": task_id_int,
                "updated_fields": updated_task.get("updated_fields", [])
            }
        )
        
        return {
            "message": "Task updated successfully",
            "task": updated_task
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        logger.warning(f"Validation error in task update: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in task update: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
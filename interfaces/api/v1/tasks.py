from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import Optional, List

from ..schemas.schemas import TaskResponse, TaskUpdate, TaskCreateRequest
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
    owner: Optional[str] = Query(None),
    priority: Optional[str] = Query(None, regex="^(low|medium|high|urgent)$"),
    created_by: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("updated_at", regex="^(created_at|updated_at|title|priority|due_date)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    limit: Optional[int] = Query(50, ge=1, le=200)
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
            priority_filter=priority,
            created_by_filter=created_by,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit
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

@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new task
    """
    try:
        # Create task using service layer
        created_task = task_service.create_task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            due_date=task_data.due_date,
            owner=task_data.owner,
            created_by=task_data.created_by,
            document_ids=task_data.document_ids
        )
        
        # Convert to response format
        response = TaskResponse(
            id=created_task["id"],
            title=created_task["title"],
            status=created_task["status"],
            due_date=created_task["due_date"],
            owner=created_task["owner"],
            source_doc_id=created_task["source_doc_id"]
        )
        
        logger.info(
            "Task created successfully",
            extra={
                "task_id": created_task["id"],
                "title": created_task["title"],
                "priority": created_task["priority"],
                "linked_documents": created_task["linked_documents"]
            }
        )
        
        return response
        
    except ValidationException as e:
        logger.warning(f"Validation error in task creation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in task creation: {e}")
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

@router.post("/tasks/{task_id}/documents")
async def link_documents_to_task(
    task_id: str,
    document_ids: List[int],
    api_key: str = Depends(verify_api_key)
):
    """
    Link documents to a task
    """
    try:
        # Convert task_id to int
        task_id_int = int(task_id)
        
        # Link documents using repository
        success = task_service.task_repository.link_documents(task_id_int, document_ids)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or no valid documents provided")
        
        logger.info(
            "Documents linked to task successfully",
            extra={
                "task_id": task_id_int,
                "document_count": len(document_ids)
            }
        )
        
        return {
            "message": f"Successfully linked {len(document_ids)} documents to task {task_id}",
            "task_id": task_id,
            "linked_documents": len(document_ids)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Error linking documents to task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/tasks/{task_id}/documents")
async def unlink_documents_from_task(
    task_id: str,
    document_ids: List[int],
    api_key: str = Depends(verify_api_key)
):
    """
    Unlink documents from a task
    """
    try:
        # Convert task_id to int
        task_id_int = int(task_id)
        
        # Unlink documents using repository
        success = task_service.task_repository.unlink_documents(task_id_int, document_ids)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        logger.info(
            "Documents unlinked from task successfully",
            extra={
                "task_id": task_id_int,
                "document_count": len(document_ids)
            }
        )
        
        return {
            "message": f"Successfully unlinked {len(document_ids)} documents from task {task_id}",
            "task_id": task_id,
            "unlinked_documents": len(document_ids)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Error unlinking documents from task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tasks/{task_id}/documents")
async def get_task_documents(
    task_id: str
):
    """
    Get all documents linked to a task
    """
    try:
        # Convert task_id to int
        task_id_int = int(task_id)
        
        # Get linked documents using repository
        documents = task_service.task_repository.get_linked_documents(task_id_int)
        
        logger.info(
            "Retrieved linked documents for task",
            extra={
                "task_id": task_id_int,
                "document_count": len(documents)
            }
        )
        
        return {
            "task_id": task_id,
            "documents": documents,
            "count": len(documents)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Error retrieving task documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
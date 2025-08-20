"""
Task Hierarchy API Routes
Endpoints for managing hierarchical tasks, tree operations, and progress tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..database import get_db, Task
from ..services.task_hierarchy_service import TaskHierarchyService
from ..core.exceptions import ValidationException
from ..security import verify_api_key

router = APIRouter(prefix="/hierarchy", tags=["Task Hierarchy"])


# Pydantic models
class TaskCreateRequest(BaseModel):
    title: str = Field(..., max_length=255)
    parent_task_id: Optional[int] = None
    task_code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    priority: str = Field("medium", pattern="^(low|medium|high|urgent)$")
    owner: Optional[str] = Field(None, max_length=100)
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    owner: Optional[str] = Field(None, max_length=100)
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: Optional[str] = Field(None, pattern="^(new|in_progress|blocked|done)$")


class TaskMoveRequest(BaseModel):
    new_parent_id: Optional[int] = None


class ProgressUpdateRequest(BaseModel):
    progress: int = Field(..., ge=0, le=100)


# API Endpoints

@router.get("/tree")
async def get_task_tree(
    root_task_id: Optional[int] = Query(None, description="Root task ID (if None, returns all root tasks)"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get hierarchical task tree"""
    try:
        service = TaskHierarchyService(db)
        tree = service.get_task_tree(root_task_id)
        
        return {
            "success": True,
            "data": tree,
            "root_task_id": root_task_id
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/tasks")
async def create_task(
    request: TaskCreateRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Create a new task"""
    try:
        service = TaskHierarchyService(db)
        task = service.create_task(
            title=request.title,
            parent_task_id=request.parent_task_id,
            task_code=request.task_code,
            description=request.description,
            priority=request.priority,
            owner=request.owner,
            due_date=request.due_date
        )
        
        return {
            "success": True,
            "data": {
                "id": task.id,
                "title": task.title,
                "task_code": task.task_code,
                "parent_task_id": task.parent_task_id,
                "task_level": task.task_level,
                "task_path": task.task_path,
                "status": task.status,
                "priority": task.priority,
                "progress_percentage": task.progress_percentage,
                "created_at": task.created_at.isoformat() if task.created_at else None
            },
            "message": f"Task {task.task_code} created successfully"
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task_details(
    task_id: int,
    include_context: bool = Query(False, description="Include ancestors, descendants, and siblings"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get task details with optional full context"""
    try:
        service = TaskHierarchyService(db)
        
        if include_context:
            data = service.get_task_full_context(task_id)
        else:
            # Just get the task
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            data = {
                "task": {
                    "id": task.id,
                    "title": task.title,
                    "task_code": task.task_code,
                    "status": task.status,
                    "priority": task.priority,
                    "progress_percentage": task.progress_percentage,
                    "due_date": task.due_date,
                    "owner": task.owner,
                    "description": task.description,
                    "task_level": task.task_level,
                    "task_path": task.task_path,
                    "parent_task_id": task.parent_task_id,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                }
            }
        
        return {
            "success": True,
            "data": data
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks/{task_id}/children")
async def get_task_children(
    task_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get direct children of a task"""
    try:
        service = TaskHierarchyService(db)
        children = service.get_task_children(task_id)
        
        return {
            "success": True,
            "data": [
                {
                    "id": task.id,
                    "title": task.title,
                    "task_code": task.task_code,
                    "status": task.status,
                    "priority": task.priority,
                    "progress_percentage": task.progress_percentage,
                    "due_date": task.due_date,
                    "owner": task.owner,
                    "task_level": task.task_level
                }
                for task in children
            ],
            "parent_task_id": task_id,
            "children_count": len(children)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks/{task_id}/descendants")
async def get_task_descendants(
    task_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get all descendants of a task"""
    try:
        service = TaskHierarchyService(db)
        descendants = service.get_task_descendants(task_id)
        
        return {
            "success": True,
            "data": [
                {
                    "id": task.id,
                    "title": task.title,
                    "task_code": task.task_code,
                    "status": task.status,
                    "priority": task.priority,
                    "progress_percentage": task.progress_percentage,
                    "due_date": task.due_date,
                    "owner": task.owner,
                    "task_level": task.task_level,
                    "task_path": task.task_path
                }
                for task in descendants
            ],
            "root_task_id": task_id,
            "descendants_count": len(descendants)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks/{task_id}/ancestors")
async def get_task_ancestors(
    task_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get all ancestors of a task"""
    try:
        service = TaskHierarchyService(db)
        ancestors = service.get_task_ancestors(task_id)
        
        return {
            "success": True,
            "data": [
                {
                    "id": task.id,
                    "title": task.title,
                    "task_code": task.task_code,
                    "status": task.status,
                    "task_level": task.task_level,
                    "task_path": task.task_path
                }
                for task in ancestors
            ],
            "task_id": task_id,
            "ancestors_count": len(ancestors)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/tasks/{task_id}/move")
async def move_task(
    task_id: int,
    request: TaskMoveRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Move a task to a new parent"""
    try:
        service = TaskHierarchyService(db)
        task = service.move_task(task_id, request.new_parent_id)
        
        return {
            "success": True,
            "data": {
                "id": task.id,
                "title": task.title,
                "task_code": task.task_code,
                "parent_task_id": task.parent_task_id,
                "task_level": task.task_level,
                "task_path": task.task_path,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            },
            "message": f"Task {task.task_code} moved successfully"
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/tasks/{task_id}/progress")
async def update_task_progress(
    task_id: int,
    request: ProgressUpdateRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Update task progress and recalculate parent progress"""
    try:
        service = TaskHierarchyService(db)
        task = service.update_task_progress(task_id, request.progress)
        
        return {
            "success": True,
            "data": {
                "id": task.id,
                "task_code": task.task_code,
                "progress_percentage": task.progress_percentage,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            },
            "message": f"Progress updated to {request.progress}%"
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks/{task_id}/progress/calculate")
async def calculate_task_progress(
    task_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Calculate progress based on children completion"""
    try:
        service = TaskHierarchyService(db)
        progress = service.calculate_progress(task_id)
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "calculated_progress": progress
            },
            "message": f"Progress calculated: {progress}%"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    cascade: bool = Query(False, description="Delete all children recursively"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Delete a task"""
    try:
        service = TaskHierarchyService(db)
        success = service.delete_task(task_id, cascade)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "message": f"Task {task_id} deleted successfully" + (" (with children)" if cascade else "")
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks/code/{task_code}")
async def get_task_by_code(
    task_code: str,
    include_context: bool = Query(False, description="Include ancestors, descendants, and siblings"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get task by task code"""
    try:
        service = TaskHierarchyService(db)
        task = service.get_task_by_code(task_code)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with code {task_code} not found")
        
        if include_context:
            data = service.get_task_full_context(task.id)
        else:
            data = {
                "task": {
                    "id": task.id,
                    "title": task.title,
                    "task_code": task.task_code,
                    "status": task.status,
                    "priority": task.priority,
                    "progress_percentage": task.progress_percentage,
                    "due_date": task.due_date,
                    "owner": task.owner,
                    "description": task.description,
                    "task_level": task.task_level,
                    "task_path": task.task_path,
                    "parent_task_id": task.parent_task_id,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                }
            }
        
        return {
            "success": True,
            "data": data
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
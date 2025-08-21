"""Domain service for task operations - Clean Architecture"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..repositories.task_repository import ITaskRepository
from ..entities.exceptions import TaskNotFoundException, ValidationException
from ..entities.types import TaskStatus
from infrastructure.security.security import validate_task_status, validate_owner_input, validate_date_input

logger = logging.getLogger(__name__)

class TaskService:
    """Domain service for task operations following Clean Architecture"""
    
    def __init__(self, task_repository: ITaskRepository):
        self.task_repository = task_repository
    
    def get_tasks(
        self, 
        status_filter: Optional[TaskStatus] = None,
        owner_filter: Optional[str] = None,
        source_type_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get tasks with filtering
        """
        return self.task_repository.get_tasks(
            status_filter=status_filter,
            owner_filter=owner_filter,
            source_type_filter=source_type_filter,
            limit=limit
        )
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a single task by ID"""
        task_entity = self.task_repository.get_by_id(task_id)
        if not task_entity:
            return None
        
        return {
            "id": str(task_entity.id),
            "title": task_entity.title,
            "status": task_entity.status,
            "due_date": task_entity.due_date,
            "owner": task_entity.owner,
            "source_doc_id": str(task_entity.source_doc_id)
        }
    
    def update_task(
        self,
        task_id: int,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update task with validation"""
        
        # Validate inputs
        if status:
            validate_task_status(status)
        if owner:
            validate_owner_input(owner)
        if due_date:
            validate_date_input(due_date)
        
        # Get existing task
        task_entity = self.task_repository.get_by_id(task_id)
        if not task_entity:
            raise TaskNotFoundException(f"Task with ID {task_id} not found")
        
        # Update fields
        updated_fields = []
        if status and status != task_entity.status:
            task_entity.status = status
            updated_fields.append("status")
        
        if owner and owner != task_entity.owner:
            task_entity.owner = owner
            updated_fields.append("owner")
        
        if due_date and due_date != task_entity.due_date:
            task_entity.due_date = due_date
            updated_fields.append("due_date")
        
        if not updated_fields:
            raise ValidationException("No fields to update")
        
        # Save via repository
        updated_task = self.task_repository.update(task_entity)
        
        return {
            "id": str(updated_task.id),
            "title": updated_task.title,
            "status": updated_task.status,
            "due_date": updated_task.due_date,
            "owner": updated_task.owner,
            "source_doc_id": str(updated_task.source_doc_id),
            "updated_fields": updated_fields
        }
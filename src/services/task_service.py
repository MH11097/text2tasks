"""Service layer cho task operations - DRY principle"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..database import Task, Document, SessionLocal
from ..core.exceptions import TaskNotFoundException, ValidationException
from ..core.types import TaskStatus
from ..security import validate_task_status, validate_owner_input, validate_date_input

logger = logging.getLogger(__name__)

class TaskService:
    """Service để xử lý task operations với DRY principle"""
    
    async def get_tasks(
        self, 
        status_filter: Optional[TaskStatus] = None,
        owner_filter: Optional[str] = None,
        source_type_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get tasks với filtering
        DRY: Centralized task querying logic
        """
        async with self._get_db_session() as db:
            query_obj = db.query(Task).join(Document, Task.source_doc_id == Document.id)
            
            # Apply filters
            if status_filter:
                query_obj = query_obj.filter(Task.status == status_filter.value)
            
            if owner_filter:
                query_obj = query_obj.filter(Task.owner == owner_filter)
            
            if source_type_filter:
                query_obj = query_obj.filter(Document.source_type == source_type_filter)
            
            tasks = query_obj.order_by(Task.created_at.desc()).limit(limit).all()
            
            # Convert to dict format
            results = []
            for task in tasks:
                results.append({
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "due_date": task.due_date,
                    "owner": task.owner,
                    "source_doc_id": str(task.source_doc_id),
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "blockers": task.blockers,
                    "project_hint": task.project_hint
                })
            
            return results
    
    async def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        async with self._get_db_session() as db:
            return db.query(Task).filter(Task.id == task_id).first()
    
    async def update_task(
        self,
        task_id: int,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update task với validation
        DRY: Centralized task update logic
        """
        async with self._get_db_session() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                raise TaskNotFoundException(f"Task {task_id} not found")
            
            # Validate và update fields
            updated_fields = []
            
            if status is not None:
                validated_status = validate_task_status(status)
                task.status = validated_status
                updated_fields.append("status")
            
            if owner is not None:
                validated_owner = validate_owner_input(owner)
                task.owner = validated_owner
                updated_fields.append("owner")
            
            if due_date is not None:
                validated_date = validate_date_input(due_date)
                task.due_date = validated_date
                updated_fields.append("due_date")
            
            task.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(
                "Task updated successfully",
                extra={
                    "task_id": task_id,
                    "updated_fields": updated_fields
                }
            )
            
            return {
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "due_date": task.due_date,
                "owner": task.owner,
                "source_doc_id": str(task.source_doc_id),
                "updated_fields": updated_fields
            }
    
    async def get_task_counts_by_status(self) -> Dict[str, int]:
        """
        Get task counts by status
        DRY: Reusable statistics logic
        """
        async with self._get_db_session() as db:
            counts = {}
            
            for status in TaskStatus:
                count = db.query(Task).filter(Task.status == status.value).count()
                counts[status.value] = count
            
            return counts
    
    async def get_tasks_by_owner(self, owner: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tasks by owner"""
        return await self.get_tasks(owner_filter=owner, limit=limit)
    
    async def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks that are overdue"""
        from datetime import date
        today = date.today().isoformat()
        
        async with self._get_db_session() as db:
            tasks = db.query(Task).filter(
                Task.due_date < today,
                Task.status.in_([TaskStatus.NEW.value, TaskStatus.IN_PROGRESS.value])
            ).all()
            
            results = []
            for task in tasks:
                results.append({
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "due_date": task.due_date,
                    "owner": task.owner,
                    "days_overdue": (date.today() - date.fromisoformat(task.due_date)).days
                })
            
            return results
    
    async def _get_db_session(self):
        """Helper để get DB session - DRY"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
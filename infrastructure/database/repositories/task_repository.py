"""Concrete implementation of task repository"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date

from domain.repositories.task_repository import ITaskRepository
from domain.entities.task import TaskEntity
from domain.entities.types import TaskStatus, SourceType
from ..models import Task, Document
from ..connection import SessionLocal

class TaskRepository(ITaskRepository):
    """SQLAlchemy implementation of task repository"""
    
    async def create(self, task: TaskEntity) -> TaskEntity:
        """Create a new task"""
        async with SessionLocal() as db:
            db_task = Task(
                title=task.title,
                status=task.status,
                due_date=task.due_date,
                owner=task.owner,
                blockers=task.blockers,
                project_hint=task.project_hint,
                source_doc_id=task.source_doc_id
            )
            db.add(db_task)
            await db.flush()
            
            # Convert back to entity
            task.id = db_task.id
            task.created_at = db_task.created_at
            task.updated_at = db_task.updated_at
            
            await db.commit()
            return task
    
    async def get_by_id(self, task_id: int) -> Optional[TaskEntity]:
        """Get task by ID"""
        async with SessionLocal() as db:
            db_task = db.query(Task).filter(Task.id == task_id).first()
            if not db_task:
                return None
            
            return TaskEntity.from_orm(db_task)
    
    async def get_tasks(
        self,
        status_filter: Optional[TaskStatus] = None,
        owner_filter: Optional[str] = None,
        source_type_filter: Optional[SourceType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get tasks with filters"""
        async with SessionLocal() as db:
            query = db.query(Task).join(Document)
            
            # Apply filters
            if status_filter:
                query = query.filter(Task.status == status_filter.value)
            if owner_filter:
                query = query.filter(Task.owner == owner_filter)
            if source_type_filter:
                query = query.filter(Document.source_type == source_type_filter.value)
            
            query = query.order_by(desc(Task.updated_at)).limit(limit)
            tasks = query.all()
            
            # Convert to dict format
            results = []
            for task in tasks:
                results.append({
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "due_date": task.due_date,
                    "owner": task.owner,
                    "blockers": task.blockers or [],
                    "project_hint": task.project_hint,
                    "source_doc_id": str(task.source_doc_id),
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                })
            
            return results
    
    async def update(self, task: TaskEntity) -> TaskEntity:
        """Update task"""
        async with SessionLocal() as db:
            db_task = db.query(Task).filter(Task.id == task.id).first()
            if not db_task:
                raise ValueError(f"Task {task.id} not found")
            
            # Update fields
            db_task.title = task.title
            db_task.status = task.status
            db_task.due_date = task.due_date
            db_task.owner = task.owner
            db_task.blockers = task.blockers
            db_task.project_hint = task.project_hint
            
            await db.commit()
            return TaskEntity.from_orm(db_task)
    
    async def get_counts_by_status(self) -> Dict[str, int]:
        """Get task counts grouped by status"""
        async with SessionLocal() as db:
            counts = {
                "new": db.query(Task).filter(Task.status == "new").count(),
                "in_progress": db.query(Task).filter(Task.status == "in_progress").count(),
                "blocked": db.query(Task).filter(Task.status == "blocked").count(),
                "done": db.query(Task).filter(Task.status == "done").count(),
            }
            return counts
    
    async def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get overdue tasks"""
        async with SessionLocal() as db:
            today = date.today()
            overdue_tasks = db.query(Task).filter(
                Task.due_date.isnot(None),
                Task.status.in_(["new", "in_progress", "blocked"])
            ).all()
            
            results = []
            for task in overdue_tasks:
                try:
                    task_date = date.fromisoformat(task.due_date)
                    if task_date < today:
                        days_overdue = (today - task_date).days
                        results.append({
                            "id": str(task.id),
                            "title": task.title,
                            "status": task.status,
                            "due_date": task.due_date,
                            "owner": task.owner,
                            "days_overdue": days_overdue
                        })
                except ValueError:
                    continue  # Skip invalid date formats
            
            return results
    
    async def delete(self, task_id: int) -> bool:
        """Delete task"""
        async with SessionLocal() as db:
            db_task = db.query(Task).filter(Task.id == task_id).first()
            if not db_task:
                return False
            
            db.delete(db_task)
            await db.commit()
            return True
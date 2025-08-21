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
    
    def create(self, task: TaskEntity) -> TaskEntity:
        """Create a new task"""
        db = SessionLocal()
        try:
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
            db.flush()
            
            # Convert back to entity
            task.id = db_task.id
            task.created_at = db_task.created_at
            task.updated_at = db_task.updated_at
            
            db.commit()
            return task
        finally:
            db.close()
    
    def get_by_id(self, task_id: int) -> Optional[TaskEntity]:
        """Get task by ID"""
        db = SessionLocal()
        try:
            db_task = db.query(Task).filter(Task.id == task_id).first()
            if not db_task:
                return None
            
            return TaskEntity(
                id=db_task.id,
                title=db_task.title,
                status=db_task.status,
                due_date=db_task.due_date,
                owner=db_task.owner,
                blockers=db_task.blockers or [],
                project_hint=db_task.project_hint,
                source_doc_id=db_task.source_doc_id,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at
            )
        finally:
            db.close()
    
    def get_tasks(
        self,
        status_filter: Optional[TaskStatus] = None,
        owner_filter: Optional[str] = None,
        source_type_filter: Optional[SourceType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get tasks with filters"""
        db = SessionLocal()
        try:
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
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                })
            
            return results
        finally:
            db.close()
    
    def update(self, task: TaskEntity) -> TaskEntity:
        """Update task"""
        db = SessionLocal()
        try:
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
            
            db.commit()
            
            return TaskEntity(
                id=db_task.id,
                title=db_task.title,
                status=db_task.status,
                due_date=db_task.due_date,
                owner=db_task.owner,
                blockers=db_task.blockers or [],
                project_hint=db_task.project_hint,
                source_doc_id=db_task.source_doc_id,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at
            )
        finally:
            db.close()
    
    def get_counts_by_status(self) -> Dict[str, int]:
        """Get task counts grouped by status"""
        db = SessionLocal()
        try:
            counts = {
                "new": db.query(Task).filter(Task.status == "new").count(),
                "in_progress": db.query(Task).filter(Task.status == "in_progress").count(),
                "blocked": db.query(Task).filter(Task.status == "blocked").count(),
                "done": db.query(Task).filter(Task.status == "done").count(),
            }
            return counts
        finally:
            db.close()
    
    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get overdue tasks"""
        db = SessionLocal()
        try:
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
        finally:
            db.close()
    
    def delete(self, task_id: int) -> bool:
        """Delete task"""
        db = SessionLocal()
        try:
            db_task = db.query(Task).filter(Task.id == task_id).first()
            if not db_task:
                return False
            
            db.delete(db_task)
            db.commit()
            return True
        finally:
            db.close()
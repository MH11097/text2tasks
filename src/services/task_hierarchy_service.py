"""
Task Hierarchy Service
Handles hierarchical task operations including tree traversal, progress calculation, and path management.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import Task, SessionLocal
from ..core.exceptions import ValidationException


class TaskHierarchyService:
    """Service for managing task hierarchies"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def create_task(
        self, 
        title: str, 
        parent_task_id: Optional[int] = None,
        task_code: Optional[str] = None,
        description: Optional[str] = None,
        priority: str = "medium",
        owner: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Task:
        """Create a new task with proper hierarchy setup"""
        
        # Generate task code if not provided
        if not task_code:
            # Get next available number
            result = self.db.execute(
                text("SELECT COUNT(*) + 1 FROM tasks")
            ).fetchone()
            task_code = f"TASK-{result[0]:03d}"
        
        # Check if task code already exists
        existing = self.db.query(Task).filter(Task.task_code == task_code).first()
        if existing:
            raise ValidationException(f"Task code {task_code} already exists")
        
        # Calculate level and path
        task_level = 0
        task_path = task_code
        
        if parent_task_id:
            parent_task = self.db.query(Task).filter(Task.id == parent_task_id).first()
            if not parent_task:
                raise ValidationException(f"Parent task {parent_task_id} not found")
            
            task_level = parent_task.task_level + 1
            task_path = f"{parent_task.task_path}/{task_code}"
        
        # Create task
        task = Task(
            title=title,
            task_code=task_code,
            parent_task_id=parent_task_id,
            task_level=task_level,
            task_path=task_path,
            description=description,
            priority=priority,
            owner=owner,
            due_date=due_date,
            progress_percentage=0,
            status="new"
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def get_task_tree(self, root_task_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get hierarchical task tree starting from root_task_id (or all root tasks if None)"""
        
        if root_task_id:
            root_tasks = [self.db.query(Task).filter(Task.id == root_task_id).first()]
            if not root_tasks[0]:
                raise ValidationException(f"Task {root_task_id} not found")
        else:
            # Get all root tasks (no parent)
            root_tasks = self.db.query(Task).filter(Task.parent_task_id.is_(None)).all()
        
        def build_tree_node(task: Task) -> Dict[str, Any]:
            # Get children
            children = self.db.query(Task).filter(Task.parent_task_id == task.id).all()
            
            return {
                "id": task.id,
                "title": task.title,
                "task_code": task.task_code,
                "status": task.status,
                "priority": task.priority,
                "progress_percentage": task.progress_percentage,
                "due_date": task.due_date,
                "owner": task.owner,
                "task_level": task.task_level,
                "task_path": task.task_path,
                "description": task.description,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "children": [build_tree_node(child) for child in children]
            }
        
        return [build_tree_node(task) for task in root_tasks if task]
    
    def get_task_children(self, task_id: int) -> List[Task]:
        """Get direct children of a task"""
        return self.db.query(Task).filter(Task.parent_task_id == task_id).all()
    
    def get_task_descendants(self, task_id: int) -> List[Task]:
        """Get all descendants of a task (recursive)"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return []
        
        # Use task_path to find all descendants efficiently
        descendants = self.db.query(Task).filter(
            Task.task_path.like(f"{task.task_path}/%")
        ).all()
        
        return descendants
    
    def get_task_ancestors(self, task_id: int) -> List[Task]:
        """Get all ancestors of a task"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task or not task.parent_task_id:
            return []
        
        ancestors = []
        current_task = task
        
        while current_task.parent_task_id:
            parent = self.db.query(Task).filter(Task.id == current_task.parent_task_id).first()
            if parent:
                ancestors.append(parent)
                current_task = parent
            else:
                break
        
        return list(reversed(ancestors))  # Return from root to immediate parent
    
    def move_task(self, task_id: int, new_parent_id: Optional[int]) -> Task:
        """Move a task to a new parent (or make it root if new_parent_id is None)"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValidationException(f"Task {task_id} not found")
        
        # Check for circular reference
        if new_parent_id:
            new_parent = self.db.query(Task).filter(Task.id == new_parent_id).first()
            if not new_parent:
                raise ValidationException(f"Parent task {new_parent_id} not found")
            
            # Check if new_parent is a descendant of task (would create circular reference)
            descendants = self.get_task_descendants(task_id)
            if any(d.id == new_parent_id for d in descendants):
                raise ValidationException("Cannot move task: would create circular reference")
        
        # Update task
        old_path = task.task_path
        old_level = task.task_level
        
        task.parent_task_id = new_parent_id
        
        if new_parent_id:
            new_parent = self.db.query(Task).filter(Task.id == new_parent_id).first()
            task.task_level = new_parent.task_level + 1
            task.task_path = f"{new_parent.task_path}/{task.task_code}"
        else:
            task.task_level = 0
            task.task_path = task.task_code
        
        # Update all descendants' paths and levels
        level_diff = task.task_level - old_level
        descendants = self.db.query(Task).filter(
            Task.task_path.like(f"{old_path}/%")
        ).all()
        
        for descendant in descendants:
            # Update path
            relative_path = descendant.task_path[len(old_path):]
            descendant.task_path = f"{task.task_path}{relative_path}"
            
            # Update level
            descendant.task_level += level_diff
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def calculate_progress(self, task_id: int) -> int:
        """Calculate progress based on children completion"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return 0
        
        children = self.get_task_children(task_id)
        
        if not children:
            # Leaf task - return its own progress
            return task.progress_percentage or 0
        
        # Calculate based on children
        total_progress = sum(child.progress_percentage or 0 for child in children)
        avg_progress = total_progress // len(children) if children else 0
        
        # Update task progress
        task.progress_percentage = avg_progress
        self.db.commit()
        
        return avg_progress
    
    def update_task_progress(self, task_id: int, progress: int) -> Task:
        """Update task progress and recalculate parent progress"""
        if not (0 <= progress <= 100):
            raise ValidationException("Progress must be between 0 and 100")
        
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValidationException(f"Task {task_id} not found")
        
        task.progress_percentage = progress
        self.db.commit()
        
        # Recalculate parent progress if exists
        if task.parent_task_id:
            self.calculate_progress(task.parent_task_id)
        
        return task
    
    def delete_task(self, task_id: int, cascade: bool = False) -> bool:
        """Delete a task. If cascade=True, delete all children too."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        if not cascade:
            # Check if task has children
            children = self.get_task_children(task_id)
            if children:
                raise ValidationException(
                    f"Cannot delete task with children. "
                    f"Either delete children first or use cascade=True"
                )
        else:
            # Delete all descendants first (bottom-up)
            descendants = self.get_task_descendants(task_id)
            # Sort by level (deepest first)
            descendants.sort(key=lambda t: t.task_level, reverse=True)
            for descendant in descendants:
                self.db.delete(descendant)
        
        self.db.delete(task)
        self.db.commit()
        
        return True
    
    def get_task_by_code(self, task_code: str) -> Optional[Task]:
        """Get task by task_code"""
        return self.db.query(Task).filter(Task.task_code == task_code).first()
    
    def get_task_full_context(self, task_id: int) -> Dict[str, Any]:
        """Get task with full context (ancestors + descendants + siblings)"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValidationException(f"Task {task_id} not found")
        
        ancestors = self.get_task_ancestors(task_id)
        descendants = self.get_task_descendants(task_id)
        
        # Get siblings
        siblings = []
        if task.parent_task_id:
            siblings = [
                t for t in self.get_task_children(task.parent_task_id)
                if t.id != task_id
            ]
        
        return {
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
                "created_at": task.created_at.isoformat() if task.created_at else None
            },
            "ancestors": [
                {
                    "id": t.id,
                    "title": t.title,
                    "task_code": t.task_code,
                    "task_level": t.task_level
                } for t in ancestors
            ],
            "descendants": [
                {
                    "id": t.id,
                    "title": t.title,
                    "task_code": t.task_code,
                    "task_level": t.task_level,
                    "status": t.status,
                    "progress_percentage": t.progress_percentage
                } for t in descendants
            ],
            "siblings": [
                {
                    "id": t.id,
                    "title": t.title,
                    "task_code": t.task_code,
                    "status": t.status,
                    "progress_percentage": t.progress_percentage
                } for t in siblings
            ]
        }
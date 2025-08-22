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
                description=task.description,
                status=task.status,
                priority=task.priority,
                due_date=task.due_date,
                owner=task.owner,
                blockers=task.blockers,
                project_hint=task.project_hint,
                source_doc_id=task.source_doc_id,
                created_by=task.created_by
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
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
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
                description=db_task.description,
                status=db_task.status,
                priority=db_task.priority,
                due_date=db_task.due_date,
                owner=db_task.owner,
                blockers=db_task.blockers or [],
                project_hint=db_task.project_hint,
                source_doc_id=db_task.source_doc_id,
                created_by=db_task.created_by,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at
            )
        finally:
            db.close()
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def get_tasks(
        self,
        status_filter: Optional[TaskStatus] = None,
        owner_filter: Optional[str] = None,
        source_type_filter: Optional[SourceType] = None,
        priority_filter: Optional[str] = None,
        created_by_filter: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get tasks with filters"""
        db = SessionLocal()
        try:
            query = db.query(Task).outerjoin(Document, Task.source_doc_id == Document.id)
            
            # Apply filters
            if status_filter:
                query = query.filter(Task.status == status_filter.value)
            if owner_filter:
                query = query.filter(Task.owner == owner_filter)
            if priority_filter:
                query = query.filter(Task.priority == priority_filter)
            if created_by_filter:
                query = query.filter(Task.created_by == created_by_filter)
            if source_type_filter:
                query = query.filter(Document.source_type == source_type_filter.value)
            
            # Apply sorting
            sort_column = getattr(Task, sort_by, Task.updated_at)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
                
            query = query.limit(limit)
            tasks = query.all()
            
            # Convert to dict format
            results = []
            for task in tasks:
                results.append({
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date,
                    "owner": task.owner,
                    "blockers": task.blockers or [],
                    "project_hint": task.project_hint,
                    "source_doc_id": str(task.source_doc_id) if task.source_doc_id else None,
                    "created_by": task.created_by,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                })
            
            return results
        finally:
            db.close()
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
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
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
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
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
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
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
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
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def link_documents(self, task_id: int, document_ids: List[int], created_by: Optional[str] = None) -> bool:
        """Link documents to a task"""
        if not document_ids:
            return True
            
        db = SessionLocal()
        try:
            from ..models import task_documents
            from datetime import datetime
            
            # Check if task exists
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return False
            
            # Check which documents exist
            existing_docs = db.query(Document.id).filter(Document.id.in_(document_ids)).all()
            existing_doc_ids = [doc.id for doc in existing_docs]
            
            if not existing_doc_ids:
                return False
            
            # Insert links (ignore duplicates due to unique constraint)
            for doc_id in existing_doc_ids:
                try:
                    db.execute(
                        task_documents.insert().values(
                            task_id=task_id,
                            document_id=doc_id,
                            created_at=datetime.utcnow(),
                            created_by=created_by
                        )
                    )
                except Exception:
                    # Ignore duplicate key errors
                    continue
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def unlink_documents(self, task_id: int, document_ids: List[int]) -> bool:
        """Unlink documents from a task"""
        if not document_ids:
            return True
            
        db = SessionLocal()
        try:
            from ..models import task_documents
            
            db.execute(
                task_documents.delete().where(
                    (task_documents.c.task_id == task_id) & 
                    (task_documents.c.document_id.in_(document_ids))
                )
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def get_linked_documents(self, task_id: int) -> List[Dict[str, Any]]:
        """Get documents linked to a task"""
        db = SessionLocal()
        try:
            from ..models import task_documents
            
            result = db.query(
                Document.id,
                Document.text,
                Document.summary,
                Document.source,
                Document.source_type,
                Document.created_at,
                task_documents.c.created_at.label('linked_at')
            ).join(
                task_documents, Document.id == task_documents.c.document_id
            ).filter(
                task_documents.c.task_id == task_id
            ).all()
            
            return [
                {
                    "id": doc.id,
                    "text": doc.text[:200] + "..." if len(doc.text) > 200 else doc.text,
                    "summary": doc.summary,
                    "source": doc.source,
                    "source_type": doc.source_type,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "linked_at": doc.linked_at.isoformat() if doc.linked_at else None
                }
                for doc in result
            ]
        finally:
            db.close()
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def get_tasks_for_document(self, document_id: int) -> List[Dict[str, Any]]:
        """Get tasks linked to a document"""
        db = SessionLocal()
        try:
            from ..models import task_documents
            
            result = db.query(
                Task.id,
                Task.title,
                Task.description,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                Task.created_by,
                Task.created_at,
                task_documents.c.created_at.label('linked_at')
            ).join(
                task_documents, Task.id == task_documents.c.task_id
            ).filter(
                task_documents.c.document_id == document_id
            ).all()
            
            return [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date,
                    "owner": task.owner,
                    "created_by": task.created_by,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "linked_at": task.linked_at.isoformat() if task.linked_at else None
                }
                for task in result
            ]
        finally:
            db.close()
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def link_tasks_to_document(self, document_id: int, task_ids: List[int], created_by: Optional[str] = None) -> bool:
        """Link tasks to a document"""
        if not task_ids:
            return True
            
        db = SessionLocal()
        try:
            from ..models import task_documents
            from datetime import datetime
            
            # Check if document exists
            doc = db.query(Document).filter(Document.id == document_id).first()
            if not doc:
                return False
            
            # Check which tasks exist
            existing_tasks = db.query(Task.id).filter(Task.id.in_(task_ids)).all()
            existing_task_ids = [task.id for task in existing_tasks]
            
            if not existing_task_ids:
                return False
            
            # Insert links (ignore duplicates due to unique constraint)
            for task_id in existing_task_ids:
                try:
                    db.execute(
                        task_documents.insert().values(
                            task_id=task_id,
                            document_id=document_id,
                            created_at=datetime.utcnow(),
                            created_by=created_by
                        )
                    )
                except Exception:
                    # Ignore duplicate key errors
                    continue
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def unlink_tasks_from_document(self, document_id: int, task_ids: List[int]) -> bool:
        """Unlink tasks from a document"""
        if not task_ids:
            return True
            
        db = SessionLocal()
        try:
            from ..models import task_documents
            
            db.execute(
                task_documents.delete().where(
                    (task_documents.c.document_id == document_id) & 
                    (task_documents.c.task_id.in_(task_ids))
                )
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        if dependent_task_id == prerequisite_task_id:
            return False  # Task cannot depend on itself
            
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            from datetime import datetime
            
            # Check if both tasks exist
            dependent_task = db.query(Task).filter(Task.id == dependent_task_id).first()
            prerequisite_task = db.query(Task).filter(Task.id == prerequisite_task_id).first()
            
            if not dependent_task or not prerequisite_task:
                return False
            
            # Check if dependency already exists
            existing = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new dependency
            dependency = TaskDependency(
                dependent_task_id=dependent_task_id,
                prerequisite_task_id=prerequisite_task_id,
                dependency_type=dependency_type,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            db.add(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependency = db.query(TaskDependency).filter(
                TaskDependency.dependent_task_id == dependent_task_id,
                TaskDependency.prerequisite_task_id == prerequisite_task_id
            ).first()
            
            if not dependency:
                return False
            
            db.delete(dependency)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependencies = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.prerequisite_task_id
            ).filter(
                TaskDependency.dependent_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependencies
            ]
            
        finally:
            db.close()
    
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            dependents = db.query(
                Task.id,
                Task.title,
                Task.status,
                Task.priority,
                Task.due_date,
                Task.owner,
                TaskDependency.dependency_type,
                TaskDependency.description,
                TaskDependency.created_at.label('dependency_created_at')
            ).join(
                TaskDependency, Task.id == TaskDependency.dependent_task_id
            ).filter(
                TaskDependency.prerequisite_task_id == task_id
            ).all()
            
            return [
                {
                    "id": dep.id,
                    "title": dep.title,
                    "status": dep.status,
                    "priority": dep.priority,
                    "due_date": dep.due_date,
                    "owner": dep.owner,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "dependency_created_at": dep.dependency_created_at.isoformat() if dep.dependency_created_at else None
                }
                for dep in dependents
            ]
            
        finally:
            db.close()
    
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        db = SessionLocal()
        try:
            from ..models import TaskDependency
            
            query = db.query(TaskDependency)
            if task_ids:
                query = query.filter(
                    (TaskDependency.dependent_task_id.in_(task_ids)) |
                    (TaskDependency.prerequisite_task_id.in_(task_ids))
                )
            
            dependencies = query.all()
            
            # Build the dependency graph
            graph = {
                "nodes": {},
                "edges": [],
                "cycles": [],
                "root_tasks": set(),
                "leaf_tasks": set()
            }
            
            # Get all task info involved in dependencies
            all_task_ids = set()
            for dep in dependencies:
                all_task_ids.add(dep.dependent_task_id)
                all_task_ids.add(dep.prerequisite_task_id)
            
            if all_task_ids:
                tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
                
                for task in tasks:
                    graph["nodes"][str(task.id)] = {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date,
                        "owner": task.owner
                    }
            
            # Add edges
            for dep in dependencies:
                graph["edges"].append({
                    "from": str(dep.prerequisite_task_id),
                    "to": str(dep.dependent_task_id),
                    "type": dep.dependency_type,
                    "description": dep.description
                })
            
            # Identify root and leaf tasks
            dependent_task_ids = set(dep.dependent_task_id for dep in dependencies)
            prerequisite_task_ids = set(dep.prerequisite_task_id for dep in dependencies)
            
            graph["root_tasks"] = list(str(tid) for tid in prerequisite_task_ids - dependent_task_ids)
            graph["leaf_tasks"] = list(str(tid) for tid in dependent_task_ids - prerequisite_task_ids)
            
            # Simple cycle detection (basic implementation)
            graph["cycles"] = self._detect_cycles(dependencies)
            
            return graph
            
        finally:
            db.close()
    
    def _detect_cycles(self, dependencies: List) -> List[List[str]]:
        """Simple cycle detection in dependency graph"""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            prereq = str(dep.prerequisite_task_id)
            dependent = str(dep.dependent_task_id)
            
            if prereq not in graph:
                graph[prereq] = []
            graph[prereq].append(dependent)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
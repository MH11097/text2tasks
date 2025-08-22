"""Abstract task repository interface"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.task import TaskEntity
from ..entities.types import TaskStatus, SourceType

class ITaskRepository(ABC):
    """Interface for task repository operations"""
    
    @abstractmethod
    def create(self, task: TaskEntity) -> TaskEntity:
        """Create a new task"""
        pass
    
    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[TaskEntity]:
        """Get task by ID"""
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def update(self, task: TaskEntity) -> TaskEntity:
        """Update task"""
        pass
    
    @abstractmethod
    def get_counts_by_status(self) -> Dict[str, int]:
        """Get task counts grouped by status"""
        pass
    
    @abstractmethod
    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get overdue tasks"""
        pass
    
    @abstractmethod
    def delete(self, task_id: int) -> bool:
        """Delete task"""
        pass
    
    @abstractmethod
    def link_documents(self, task_id: int, document_ids: List[int], created_by: Optional[str] = None) -> bool:
        """Link documents to a task"""
        pass
    
    @abstractmethod
    def unlink_documents(self, task_id: int, document_ids: List[int]) -> bool:
        """Unlink documents from a task"""
        pass
    
    @abstractmethod
    def get_linked_documents(self, task_id: int) -> List[Dict[str, Any]]:
        """Get documents linked to a task"""
        pass
    
    @abstractmethod
    def get_tasks_for_document(self, document_id: int) -> List[Dict[str, Any]]:
        """Get tasks linked to a document"""
        pass
    
    @abstractmethod
    def link_tasks_to_document(self, document_id: int, task_ids: List[int], created_by: Optional[str] = None) -> bool:
        """Link tasks to a document"""
        pass
    
    @abstractmethod
    def unlink_tasks_from_document(self, document_id: int, task_ids: List[int]) -> bool:
        """Unlink tasks from a document"""
        pass
    
    @abstractmethod
    def create_dependency(self, dependent_task_id: int, prerequisite_task_id: int, 
                         dependency_type: str = "blocks", description: Optional[str] = None, 
                         created_by: Optional[str] = None) -> bool:
        """Create a dependency between tasks"""
        pass
    
    @abstractmethod
    def remove_dependency(self, dependent_task_id: int, prerequisite_task_id: int) -> bool:
        """Remove a dependency between tasks"""
        pass
    
    @abstractmethod
    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that this task depends on (prerequisites)"""
        pass
    
    @abstractmethod
    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all tasks that depend on this task"""
        pass
    
    @abstractmethod
    def get_dependency_graph(self, task_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get the complete dependency graph for tasks"""
        pass
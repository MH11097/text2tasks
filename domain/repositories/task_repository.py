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
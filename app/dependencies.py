"""Dependency injection configuration"""

from functools import lru_cache
from typing import Generator

from domain.repositories.document_repository import IDocumentRepository
from domain.repositories.task_repository import ITaskRepository
from infrastructure.database.repositories.document_repository import DocumentRepository
from infrastructure.database.repositories.task_repository import TaskRepository
from infrastructure.database.connection import SessionLocal, get_db
from infrastructure.external.openai_client import LLMClient

# Repository dependencies
@lru_cache()
def get_document_repository() -> IDocumentRepository:
    """Get document repository instance"""
    return DocumentRepository()

@lru_cache()
def get_task_repository() -> ITaskRepository:
    """Get task repository instance"""
    return TaskRepository()

# Service dependencies
@lru_cache()
def get_llm_client() -> LLMClient:
    """Get LLM client instance"""
    return LLMClient()

# Database dependencies (keeping for compatibility)
def get_database() -> Generator:
    """Get database session"""
    return get_db()

# Container for dependency injection
class DependencyContainer:
    """Simple DI container for managing dependencies"""
    
    def __init__(self):
        self._document_repository = None
        self._task_repository = None
        self._llm_client = None
    
    @property
    def document_repository(self) -> IDocumentRepository:
        if self._document_repository is None:
            self._document_repository = DocumentRepository()
        return self._document_repository
    
    @property
    def task_repository(self) -> ITaskRepository:
        if self._task_repository is None:
            self._task_repository = TaskRepository()
        return self._task_repository
    
    @property
    def llm_client(self) -> LLMClient:
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client

# Global container instance
container = DependencyContainer()
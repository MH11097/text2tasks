"""Abstract document repository interface"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.document import DocumentEntity
from ..entities.types import SourceType

class IDocumentRepository(ABC):
    """Interface for document repository operations"""
    
    @abstractmethod
    async def create(self, document: DocumentEntity) -> DocumentEntity:
        """Create a new document"""
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: int) -> Optional[DocumentEntity]:
        """Get document by ID"""
        pass
    
    @abstractmethod
    async def get_by_source(
        self, 
        source_type: SourceType, 
        source_id: str,
        limit: int = 10
    ) -> List[DocumentEntity]:
        """Get documents by source"""
        pass
    
    @abstractmethod
    async def search_by_similarity(
        self, 
        embeddings: List[float],
        top_k: int = 5,
        source_type_filter: Optional[SourceType] = None
    ) -> List[Dict[str, Any]]:
        """Search documents by embedding similarity"""
        pass
    
    @abstractmethod
    async def update(self, document: DocumentEntity) -> DocumentEntity:
        """Update document"""
        pass
    
    @abstractmethod
    async def delete(self, document_id: int) -> bool:
        """Delete document"""
        pass
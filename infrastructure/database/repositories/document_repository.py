"""Concrete implementation of document repository"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from domain.repositories.document_repository import IDocumentRepository
from domain.entities.document import DocumentEntity
from domain.entities.types import SourceType
from ..models import Document, Embedding
from ..connection import SessionLocal
from infrastructure.external.openai_client import cosine_similarity

class DocumentRepository(IDocumentRepository):
    """SQLAlchemy implementation of document repository"""
    
    async def create(self, document: DocumentEntity) -> DocumentEntity:
        """Create a new document"""
        async with SessionLocal() as db:
            db_document = Document(
                text=document.text,
                source=document.source,
                source_type=document.source_type,
                source_id=document.source_id,
                metadata=document.metadata,
                summary=document.summary
            )
            db.add(db_document)
            await db.flush()
            
            # Convert back to entity
            document.id = db_document.id
            document.created_at = db_document.created_at
            
            await db.commit()
            return document
    
    async def get_by_id(self, document_id: int) -> Optional[DocumentEntity]:
        """Get document by ID"""
        async with SessionLocal() as db:
            db_document = db.query(Document).filter(Document.id == document_id).first()
            if not db_document:
                return None
            
            return DocumentEntity.from_orm(db_document)
    
    async def get_by_source(
        self, 
        source_type: SourceType, 
        source_id: str,
        limit: int = 10
    ) -> List[DocumentEntity]:
        """Get documents by source"""
        async with SessionLocal() as db:
            query = db.query(Document).filter(
                Document.source_type == source_type.value,
                Document.source_id == source_id
            ).order_by(desc(Document.created_at)).limit(limit)
            
            db_documents = query.all()
            return [DocumentEntity.from_orm(doc) for doc in db_documents]
    
    async def search_by_similarity(
        self, 
        embeddings: List[float],
        top_k: int = 5,
        source_type_filter: Optional[SourceType] = None
    ) -> List[Dict[str, Any]]:
        """Search documents by embedding similarity"""
        async with SessionLocal() as db:
            query = db.query(Document, Embedding).join(Embedding)
            
            if source_type_filter:
                query = query.filter(Document.source_type == source_type_filter.value)
            
            documents_with_embeddings = query.all()
            
            # Calculate similarities
            results = []
            for doc, embedding in documents_with_embeddings:
                similarity = cosine_similarity(embeddings, embedding.vector)
                results.append({
                    "id": doc.id,
                    "text": doc.text,
                    "summary": doc.summary,
                    "source": doc.source,
                    "source_type": doc.source_type,
                    "created_at": doc.created_at.isoformat(),
                    "similarity": similarity
                })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
    
    async def update(self, document: DocumentEntity) -> DocumentEntity:
        """Update document"""
        async with SessionLocal() as db:
            db_document = db.query(Document).filter(Document.id == document.id).first()
            if not db_document:
                raise ValueError(f"Document {document.id} not found")
            
            # Update fields
            db_document.text = document.text
            db_document.source = document.source
            db_document.source_type = document.source_type
            db_document.source_id = document.source_id
            db_document.metadata = document.metadata
            db_document.summary = document.summary
            
            await db.commit()
            return DocumentEntity.from_orm(db_document)
    
    async def delete(self, document_id: int) -> bool:
        """Delete document"""
        async with SessionLocal() as db:
            db_document = db.query(Document).filter(Document.id == document_id).first()
            if not db_document:
                return False
            
            db.delete(db_document)
            await db.commit()
            return True
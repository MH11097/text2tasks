"""Service layer cho document operations - DRY principle"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..database import Document, Embedding, Task, SessionLocal
from ..llm_client import LLMClient
from ..core.exceptions import LLMException, ValidationException, DocumentNotFoundException
from ..core.types import ProcessingResult, SourceType, DocumentSource, TaskStatus
from ..security import validate_text_input, validate_source_input

logger = logging.getLogger(__name__)

class DocumentService:
    """Service để xử lý document operations với DRY principle"""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def process_document(
        self, 
        text: str, 
        source: str,
        source_type: SourceType = SourceType.WEB,
        source_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> ProcessingResult:
        """
        Process document với full pipeline
        DRY: Consolidate document processing logic
        """
        try:
            # Validate inputs
            validated_text = validate_text_input(text)
            validated_source = validate_source_input(source)
            
            # Extract summary và actions từ LLM
            llm_result = await self.llm_client.extract_summary_and_actions(validated_text)
            
            # Generate embeddings
            embeddings = await self.llm_client.generate_embeddings(validated_text)
            
            # Save to database trong transaction
            async with self._get_db_session() as db:
                document = Document(
                    text=validated_text,
                    source=validated_source,
                    source_type=source_type.value,
                    source_id=source_id,
                    metadata=metadata or {},
                    summary=llm_result.get("summary", "")
                )
                db.add(document)
                await db.flush()  # Get document ID
                
                # Save embeddings
                embedding_record = Embedding(
                    document_id=document.id,
                    vector=embeddings
                )
                db.add(embedding_record)
                
                # Save tasks
                tasks_created = 0
                for action in llm_result.get("actions", []):
                    task = Task(
                        title=action["title"],
                        status=TaskStatus.NEW.value,
                        due_date=action.get("due"),
                        owner=action.get("owner"),
                        blockers=action.get("blockers", []),
                        project_hint=action.get("project_hint"),
                        source_doc_id=document.id
                    )
                    db.add(task)
                    tasks_created += 1
                
                await db.commit()
                
                logger.info(
                    "Document processed successfully",
                    extra={
                        "document_id": document.id,
                        "source_type": source_type.value,
                        "tasks_created": tasks_created
                    }
                )
                
                return ProcessingResult(
                    document_id=document.id,
                    summary=llm_result.get("summary", ""),
                    actions_count=tasks_created,
                    success=True
                )
                
        except Exception as e:
            logger.error(
                "Document processing failed",
                extra={
                    "error": str(e),
                    "source_type": source_type.value if source_type else None
                }
            )
            
            return ProcessingResult(
                document_id=0,
                summary="",
                actions_count=0,
                success=False,
                error_message=str(e)
            )
    
    async def search_documents_by_similarity(
        self, 
        query: str, 
        top_k: int = 6,
        source_type_filter: Optional[SourceType] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents bằng semantic similarity
        DRY: Reusable search functionality
        """
        try:
            # Generate query embeddings
            query_embeddings = await self.llm_client.generate_embeddings(query)
            
            # Search trong database
            async with self._get_db_session() as db:
                # Base query
                query_obj = db.query(Document, Embedding).join(
                    Embedding, Document.id == Embedding.document_id
                )
                
                # Filter by source type if provided
                if source_type_filter:
                    query_obj = query_obj.filter(Document.source_type == source_type_filter.value)
                
                documents_with_embeddings = query_obj.all()
                
                # Calculate similarities
                from ..llm_client import cosine_similarity
                similarities = []
                
                for doc, embedding in documents_with_embeddings:
                    similarity = cosine_similarity(query_embeddings, embedding.vector)
                    similarities.append({
                        "document": doc,
                        "similarity": similarity
                    })
                
                # Sort by similarity và return top_k
                similarities.sort(key=lambda x: x["similarity"], reverse=True)
                
                results = []
                for item in similarities[:top_k]:
                    doc = item["document"]
                    results.append({
                        "id": doc.id,
                        "text": doc.text,
                        "summary": doc.summary,
                        "source": doc.source,
                        "source_type": doc.source_type,
                        "created_at": doc.created_at,
                        "similarity": item["similarity"]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []
    
    async def get_document_by_id(self, document_id: int) -> Optional[Document]:
        """Get document by ID"""
        async with self._get_db_session() as db:
            return db.query(Document).filter(Document.id == document_id).first()
    
    async def get_documents_by_source(
        self, 
        source_type: SourceType,
        source_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Document]:
        """Get documents by source type/id"""
        async with self._get_db_session() as db:
            query_obj = db.query(Document).filter(Document.source_type == source_type.value)
            
            if source_id:
                query_obj = query_obj.filter(Document.source_id == source_id)
            
            return query_obj.order_by(Document.created_at.desc()).limit(limit).all()
    
    async def _get_db_session(self):
        """Helper để get DB session - DRY"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
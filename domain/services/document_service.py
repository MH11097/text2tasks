"""Domain service for document operations - Clean Architecture"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..repositories.document_repository import IDocumentRepository
from ..entities.document import DocumentEntity
from ..entities.types import ProcessingResult, SourceType
from ..entities.exceptions import LLMException, ValidationException
from infrastructure.security.security import validate_text_input, validate_source_input
from infrastructure.external.openai_client import LLMClient

logger = logging.getLogger(__name__)

class DocumentService:
    """Domain service for document operations following Clean Architecture"""
    
    def __init__(
        self, 
        document_repository: IDocumentRepository,
        llm_client: LLMClient
    ):
        self.document_repository = document_repository
        self.llm_client = llm_client
    
    async def process_document(
        self, 
        text: str, 
        source: str,
        source_type: SourceType = SourceType.WEB,
        source_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> ProcessingResult:
        """
        Process document with full pipeline
        Clean Architecture: Domain service orchestrates business logic
        """
        try:
            # Validate inputs
            validated_text = validate_text_input(text)
            validated_source = validate_source_input(source)
            
            # Extract summary and actions from LLM
            llm_result = await self.llm_client.extract_summary_and_actions(validated_text)
            
            # Generate embeddings
            embeddings = await self.llm_client.generate_embeddings(validated_text)
            
            # Create document entity
            document = DocumentEntity(
                text=validated_text,
                source=validated_source,
                source_type=source_type.value,
                source_id=source_id,
                metadata=metadata or {},
                summary=llm_result.get("summary", "")
            )
            
            # Save through repository
            saved_document = await self.document_repository.create(document)
            
            # Create tasks from actions
            actions_count = len(llm_result.get("actions", []))
            
            logger.info(f"Document {saved_document.id} processed successfully with {actions_count} actions")
            
            return ProcessingResult(
                document_id=saved_document.id,
                summary=saved_document.summary,
                actions_count=actions_count,
                success=True
            )
            
        except ValidationException as e:
            logger.error(f"Validation error during document processing: {e}")
            return ProcessingResult(
                document_id=0,
                summary="",
                actions_count=0,
                success=False,
                error_message=f"Validation error: {str(e)}"
            )
            
        except LLMException as e:
            logger.error(f"LLM error during document processing: {e}")
            return ProcessingResult(
                document_id=0,
                summary="",
                actions_count=0,
                success=False,
                error_message=f"LLM processing error: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during document processing: {e}")
            return ProcessingResult(
                document_id=0,
                summary="",
                actions_count=0,
                success=False,
                error_message=f"Processing error: {str(e)}"
            )
    
    async def search_documents_by_similarity(
        self,
        query: str,
        top_k: int = 5,
        source_type_filter: Optional[SourceType] = None
    ) -> List[Dict[str, Any]]:
        """Search documents by similarity"""
        try:
            # Generate query embeddings
            query_embeddings = await self.llm_client.generate_embeddings(query)
            
            # Search through repository
            results = await self.document_repository.search_by_similarity(
                query_embeddings, 
                top_k=top_k,
                source_type_filter=source_type_filter
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def get_document_by_id(self, document_id: int) -> Optional[DocumentEntity]:
        """Get document by ID"""
        return await self.document_repository.get_by_id(document_id)
    
    async def get_documents_by_source(
        self, 
        source_type: SourceType, 
        source_id: str,
        limit: int = 10
    ) -> List[DocumentEntity]:
        """Get documents by source"""
        return await self.document_repository.get_by_source(
            source_type, source_id, limit
        )
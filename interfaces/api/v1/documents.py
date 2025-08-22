from fastapi import APIRouter, Depends, HTTPException, Header, Query, UploadFile, File
from typing import Optional, List
from datetime import datetime

from ..schemas.schemas import TaskResponse
from domain.services.task_service import TaskService
from domain.services.document_service import DocumentService
from domain.entities.exceptions import ValidationException
from shared.config.settings import settings
import logging
from app.dependencies import container

router = APIRouter()
document_service = DocumentService(
    document_repository=container.document_repository,
    llm_client=container.llm_client
)
task_service = TaskService(
    task_repository=container.task_repository
)
logger = logging.getLogger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    from infrastructure.security.security import validate_api_key_header
    validated_key = validate_api_key_header(x_api_key)
    if validated_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return validated_key

@router.get("/documents")
async def list_documents(
    limit: Optional[int] = Query(50, ge=1, le=200),
    offset: Optional[int] = Query(0, ge=0)
):
    """
    List all documents with pagination
    """
    try:
        documents = await document_service.document_repository.get_all_documents(limit=limit, offset=offset)
        
        logger.info(
            "Documents listed successfully",
            extra={
                "count": len(documents),
                "limit": limit,
                "offset": offset
            }
        )
        
        return {
            "documents": documents,
            "count": len(documents),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/documents")
async def create_document(
    text: str,
    summary: Optional[str] = None,
    source: Optional[str] = "manual",
    source_type: Optional[str] = "document",
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new document
    """
    try:
        # Validate inputs
        if not text or not text.strip():
            raise ValidationException("Document text is required")
        
        if len(text) > 50000:
            raise ValidationException("Document text too long (max 50000 characters)")
        
        # Create document using repository
        created_document = await document_service.document_repository.create_document(
            text=text.strip(),
            summary=summary or "",
            source=source,
            source_type=source_type
        )
        
        logger.info(
            "Document created successfully",
            extra={
                "document_id": created_document.get("id"),
                "text_length": len(text),
                "source_type": source_type
            }
        )
        
        return {
            "message": "Document created successfully",
            "document": created_document
        }
        
    except ValidationException as e:
        logger.warning(f"Validation error in document creation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in document creation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/documents/{document_id}/tasks")
async def get_document_tasks(
    document_id: str
):
    """
    Get all tasks linked to a document
    """
    try:
        # Convert document_id to int
        document_id_int = int(document_id)
        
        # Get linked tasks using repository
        tasks = task_service.task_repository.get_tasks_for_document(document_id_int)
        
        logger.info(
            "Retrieved linked tasks for document",
            extra={
                "document_id": document_id_int,
                "task_count": len(tasks)
            }
        )
        
        return {
            "document_id": document_id,
            "tasks": tasks,
            "count": len(tasks)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    except Exception as e:
        logger.error(f"Error retrieving document tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/documents/{document_id}/tasks")
async def link_tasks_to_document(
    document_id: str,
    task_ids: List[int],
    api_key: str = Depends(verify_api_key)
):
    """
    Link tasks to a document
    """
    try:
        # Convert document_id to int
        document_id_int = int(document_id)
        
        # Link tasks using repository
        success = task_service.task_repository.link_tasks_to_document(document_id_int, task_ids)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found or no valid tasks provided")
        
        logger.info(
            "Tasks linked to document successfully",
            extra={
                "document_id": document_id_int,
                "task_count": len(task_ids)
            }
        )
        
        return {
            "message": f"Successfully linked {len(task_ids)} tasks to document {document_id}",
            "document_id": document_id,
            "linked_tasks": len(task_ids)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    except Exception as e:
        logger.error(f"Error linking tasks to document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/documents/{document_id}/tasks")
async def unlink_tasks_from_document(
    document_id: str,
    task_ids: List[int],
    api_key: str = Depends(verify_api_key)
):
    """
    Unlink tasks from a document
    """
    try:
        # Convert document_id to int
        document_id_int = int(document_id)
        
        # Unlink tasks using repository
        success = task_service.task_repository.unlink_tasks_from_document(document_id_int, task_ids)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(
            "Tasks unlinked from document successfully",
            extra={
                "document_id": document_id_int,
                "task_count": len(task_ids)
            }
        )
        
        return {
            "message": f"Successfully unlinked {len(task_ids)} tasks from document {document_id}",
            "document_id": document_id,
            "unlinked_tasks": len(task_ids)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    except Exception as e:
        logger.error(f"Error unlinking tasks from document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    summary: Optional[str] = None,
    source: Optional[str] = "upload",
    source_type: Optional[str] = "document",
    api_key: str = Depends(verify_api_key)
):
    """
    Upload a document file
    """
    try:
        # Validate file type
        allowed_types = ["text/plain", "application/pdf", "text/markdown", "application/msword", 
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        
        if file.content_type not in allowed_types:
            raise ValidationException(f"Unsupported file type: {file.content_type}")
        
        # Validate file size (50MB limit)
        if file.size and file.size > 50 * 1024 * 1024:
            raise ValidationException("File too large (max 50MB)")
        
        # Read file content
        file_content = await file.read()
        
        # Extract text from file based on type
        if file.content_type == "text/plain" or file.content_type == "text/markdown":
            text = file_content.decode('utf-8')
        elif file.content_type == "application/pdf":
            # TODO: Add PDF text extraction
            text = "PDF content extraction not yet implemented"
        else:
            # For Word documents, etc.
            # TODO: Add document parsing
            text = "Document content extraction not yet implemented"
        
        if len(text.strip()) == 0:
            raise ValidationException("Document appears to be empty")
        
        # Create document using repository
        created_document = await document_service.document_repository.create_document(
            text=text.strip(),
            summary=summary or f"Uploaded from {file.filename}",
            source=source,
            source_type=source_type
        )
        
        logger.info(
            "Document uploaded successfully",
            extra={
                "document_id": created_document.get("id"),
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": file.size,
                "text_length": len(text)
            }
        )
        
        return {
            "message": "Document uploaded successfully",
            "document": created_document,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": file.size
        }
        
    except ValidationException as e:
        logger.warning(f"Validation error in document upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in document upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional

from ..schemas.schemas import IngestRequest, IngestResponse, ActionItem
from domain.services.document_service import DocumentService
from domain.entities.types import SourceType, ProcessingResult
from domain.entities.exceptions import ValidationException, LLMException
from shared.config.settings import settings
import logging
from app.dependencies import container

router = APIRouter()
document_service = DocumentService(
    document_repository=container.document_repository,
    llm_client=container.llm_client
)
logger = logging.getLogger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    from infrastructure.security.security import validate_api_key_header
    
    validated_key = validate_api_key_header(x_api_key)
    
    if validated_key != settings.api_key:
        logger.warning("Invalid API key attempted", extra={"key_preview": validated_key[:10] + "..." if len(validated_key) > 10 else validated_key})
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return validated_key

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    http_request: Request,
    request: IngestRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Ingest document using service layer - DRY refactored
    """
    try:
        # Process document using service layer
        result = await document_service.process_document(
            text=request.text,
            source=request.source,
            source_type=SourceType.WEB,
            source_id=None,  # Web requests don't have specific source_id
            metadata={"user_agent": http_request.headers.get("user-agent")}
        )
        
        if not result.success:
            raise HTTPException(
                status_code=500, 
                detail=f"Document processing failed: {result.error_message}"
            )
        
        # Get document to extract actions for response
        document = await document_service.get_document_by_id(result.document_id)
        if not document:
            raise HTTPException(status_code=500, detail="Document created but not found")
        
        # Get tasks for this document
        from ..services.task_service import TaskService
        task_service = TaskService()
        tasks = await task_service.get_tasks(limit=100)
        
        # Filter tasks for this document
        document_tasks = [
            task for task in tasks 
            if task["source_doc_id"] == str(result.document_id)
        ]
        
        # Convert to ActionItem format
        created_actions = []
        for task in document_tasks:
            action_item = ActionItem(
                title=task["title"],
                owner=task["owner"],
                due=task["due_date"],
                blockers=task.get("blockers", []),
                project_hint=task.get("project_hint")
            )
            created_actions.append(action_item)
        
        logger.info(
            "Document ingested successfully via API",
            extra={
                "document_id": result.document_id,
                "actions_count": result.actions_count
            }
        )
        
        return IngestResponse(
            document_id=str(result.document_id),
            summary=result.summary,
            actions=created_actions
        )
        
    except ValidationException as e:
        logger.warning(f"Validation error in ingest: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except LLMException as e:
        logger.error(f"LLM error in ingest: {e}")
        raise HTTPException(status_code=502, detail="AI processing temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in ingest: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db_session, Document, Embedding, Task
from ..schemas import IngestRequest, IngestResponse, ActionItem
from ..llm_client import LLMClient
from ..config import settings
from ..logging_config import get_logger
from ..rate_limiting import write_endpoint_limit

router = APIRouter()
llm_client = LLMClient()
logger = get_logger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@router.post("/ingest", response_model=IngestResponse)
@write_endpoint_limit()
async def ingest_document(
    http_request: Request,
    request: IngestRequest,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    try:
        # Extract summary and actions using LLM
        extraction_result = await llm_client.extract_summary_and_actions(request.text)
        summary = extraction_result.get("summary", "")
        actions_data = extraction_result.get("actions", [])
        
        # Create document
        document = Document(
            text=request.text,
            source=request.source,
            summary=summary
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Generate and store embeddings
        embeddings_vector = await llm_client.generate_embeddings(request.text)
        embedding = Embedding(
            document_id=document.id,
            vector=embeddings_vector
        )
        db.add(embedding)
        
        # Create tasks from extracted actions
        created_actions = []
        for action_data in actions_data:
            # Create task in database
            task = Task(
                title=action_data.get("title", ""),
                owner=action_data.get("owner"),
                due_date=action_data.get("due"),
                blockers=action_data.get("blockers", []),
                project_hint=action_data.get("project_hint"),
                source_doc_id=document.id,
                status="new"
            )
            db.add(task)
            
            # Create response action item
            action_item = ActionItem(
                title=action_data.get("title", ""),
                owner=action_data.get("owner"),
                due=action_data.get("due"),
                blockers=action_data.get("blockers", []),
                project_hint=action_data.get("project_hint")
            )
            created_actions.append(action_item)
        
        db.commit()
        
        return IngestResponse(
            document_id=str(document.id),
            summary=summary,
            actions=created_actions
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
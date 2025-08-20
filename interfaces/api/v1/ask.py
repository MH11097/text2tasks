from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from ..schemas import AskRequest, AskResponse
from ..services.document_service import DocumentService
from ..services.task_service import TaskService
from ..core.exceptions import ValidationException, LLMException
from ..config import settings
from ..logging_config import get_logger
from ..llm_client import LLMClient

router = APIRouter()
document_service = DocumentService()
task_service = TaskService()
llm_client = LLMClient()
logger = get_logger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    from ..security import validate_api_key_header
    validated_key = validate_api_key_header(x_api_key)
    if validated_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return validated_key

@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Q&A endpoint using service layer - DRY refactored
    """
    try:
        # Search for relevant documents using service layer
        relevant_docs = await document_service.search_documents_by_similarity(
            request.question,
            top_k=request.top_k
        )
        
        if not relevant_docs:
            logger.info(f"No relevant documents found for question: {request.question[:50]}...")
            return AskResponse(
                answer="Chưa đủ thông tin trong hệ thống để trả lời câu hỏi này.",
                refs=[],
                suggested_next_steps=["Thêm tài liệu vào hệ thống", "Kiểm tra lại câu hỏi"]
            )
        
        # Check similarity threshold
        if relevant_docs[0]["similarity"] < 0.1:
            logger.info(f"Low similarity for question: {request.question[:50]}... (max: {relevant_docs[0]['similarity']})")
            return AskResponse(
                answer="Chưa đủ thông tin trong hệ thống để trả lời câu hỏi này.",
                refs=[],
                suggested_next_steps=["Thêm tài liệu liên quan", "Diễn đạt lại câu hỏi"]
            )
        
        # Build context from documents
        context_parts = []
        document_refs = []
        
        # Add summaries
        context_parts.append("Summaries (tối đa 5 mục)")
        for doc in relevant_docs[:5]:
            if doc["summary"]:
                context_parts.append(f"- {doc['summary']}")
                document_refs.append(str(doc["id"]))
        
        # Add text snippets
        context_parts.append("\nTrích đoạn gốc ngắn có chứa từ khoá (≤ 600 từ tổng)")
        total_words = 0
        max_words = 400
        
        for doc in relevant_docs[:3]:
            if total_words >= max_words:
                break
            
            words = doc["text"].split()
            snippet_words = words[:min(100, max_words - total_words)]
            snippet = " ".join(snippet_words)
            
            if snippet:
                context_parts.append(f"- {snippet}...")
                total_words += len(snippet_words)
        
        # Add related tasks using service layer
        doc_ids = [str(doc["id"]) for doc in relevant_docs]
        all_tasks = await task_service.get_tasks(limit=50)
        
        # Filter tasks related to these documents
        related_tasks = [
            task for task in all_tasks
            if task["source_doc_id"] in doc_ids
        ]
        
        if related_tasks:
            context_parts.append("\nTasks liên quan (title/status/due/owner)")
            for task in related_tasks[:5]:
                task_info = f"- {task['title']} (status: {task['status']}"
                if task["due_date"]:
                    task_info += f", due: {task['due_date']}"
                if task["owner"]:
                    task_info += f", owner: {task['owner']}"
                task_info += ")"
                context_parts.append(task_info)
        
        context = "\n".join(context_parts)
        
        # Generate answer using LLM
        answer_result = await llm_client.answer_question(request.question, context)
        
        logger.info(
            "Question answered successfully",
            extra={
                "question_preview": request.question[:50],
                "relevant_docs_count": len(relevant_docs),
                "related_tasks_count": len(related_tasks)
            }
        )
        
        return AskResponse(
            answer=answer_result.get("answer", "Không thể tạo câu trả lời."),
            refs=list(set(document_refs)),
            suggested_next_steps=answer_result.get("suggested_next_steps", [])
        )
        
    except ValidationException as e:
        logger.warning(f"Validation error in ask: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except LLMException as e:
        logger.error(f"LLM error in ask: {e}")
        raise HTTPException(status_code=502, detail="AI processing temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in ask: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
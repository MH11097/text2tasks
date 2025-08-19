from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Tuple

from ..database import get_db_session, Document, Embedding, Task
from ..schemas import AskRequest, AskResponse
from ..llm_client import LLMClient, cosine_similarity
from ..config import settings

router = APIRouter()
llm_client = LLMClient()

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    from ..security import validate_api_key_header
    validated_key = validate_api_key_header(x_api_key)
    if validated_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return validated_key

@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    try:
        # Generate embedding for the question
        question_embedding = await llm_client.generate_embeddings(request.question)
        
        # Retrieve all documents with embeddings
        documents_with_embeddings = db.query(Document, Embedding).join(
            Embedding, Document.id == Embedding.document_id
        ).all()
        
        if not documents_with_embeddings:
            return AskResponse(
                answer="Chưa đủ thông tin trong hệ thống để trả lời câu hỏi này.",
                refs=[],
                suggested_next_steps=["Thêm tài liệu vào hệ thống", "Kiểm tra lại câu hỏi"]
            )
        
        # Calculate similarities and get top-k documents
        similarities: List[Tuple[float, Document]] = []
        
        for document, embedding in documents_with_embeddings:
            similarity = cosine_similarity(question_embedding, embedding.vector)
            similarities.append((similarity, document))
        
        # Sort by similarity and take top-k
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_documents = similarities[:request.top_k]
        
        # Check if we have sufficient similarity (threshold)
        if not top_documents or top_documents[0][0] < 0.1:
            return AskResponse(
                answer="Chưa đủ thông tin trong hệ thống để trả lời câu hỏi này.",
                refs=[],
                suggested_next_steps=["Thêm tài liệu liên quan", "Diễn đạt lại câu hỏi"]
            )
        
        # Build context from top documents
        context_parts = []
        document_refs = []
        
        # Add summaries
        context_parts.append("Summaries (tối đa 5 mục)")
        for i, (similarity, doc) in enumerate(top_documents[:5]):
            if doc.summary:
                context_parts.append(f"- {doc.summary}")
                document_refs.append(str(doc.id))
        
        # Add relevant text snippets (limited to ~400 words total)
        context_parts.append("\nTrích đoạn gốc ngắn có chứa từ khoá (≤ 600 từ tổng)")
        total_words = 0
        max_words = 400
        
        for similarity, doc in top_documents[:3]:  # Limit to top 3 for snippets
            if total_words >= max_words:
                break
                
            # Extract relevant snippet (first 100 words)
            words = doc.text.split()
            snippet_words = words[:min(100, max_words - total_words)]
            snippet = " ".join(snippet_words)
            
            if snippet:
                context_parts.append(f"- {snippet}...")
                total_words += len(snippet_words)
        
        # Add related tasks
        doc_ids = [str(doc.id) for _, doc in top_documents]
        if doc_ids:
            tasks = db.query(Task).filter(Task.source_doc_id.in_([int(d) for d in doc_ids])).all()
            
            if tasks:
                context_parts.append("\nTasks liên quan (title/status/due/owner)")
                for task in tasks[:5]:  # Limit to 5 tasks
                    task_info = f"- {task.title} (status: {task.status}"
                    if task.due_date:
                        task_info += f", due: {task.due_date}"
                    if task.owner:
                        task_info += f", owner: {task.owner}"
                    task_info += ")"
                    context_parts.append(task_info)
        
        context = "\n".join(context_parts)
        
        # Generate answer using LLM
        answer_result = await llm_client.answer_question(request.question, context)
        
        return AskResponse(
            answer=answer_result.get("answer", "Không thể tạo câu trả lời."),
            refs=list(set(document_refs)),  # Remove duplicates
            suggested_next_steps=answer_result.get("suggested_next_steps", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
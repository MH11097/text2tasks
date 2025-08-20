"""
Contextual Ask API Routes
Advanced Q&A endpoints with task-specific context and scope management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from ..database import get_db, Task
from ..services.contextual_qa_service import ContextualQAService
from ..core.exceptions import ValidationException
from ..security import verify_api_key

router = APIRouter(prefix="/ask", tags=["Contextual Q&A"])


# Pydantic models
class TaskAskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    scope: str = Field("self", pattern="^(self|subtasks|tree|inherit)$")
    top_k: int = Field(6, ge=1, le=20)


class TaskAskResponse(BaseModel):
    answer: str
    task_context: dict
    context_summary: dict
    refs: list
    suggested_next_steps: list


class EnhancedAskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    task_code: Optional[str] = Field(None, description="Optional task code for context")
    scope: str = Field("self", pattern="^(self|subtasks|tree|inherit)$")
    top_k: int = Field(6, ge=1, le=20)


# API Endpoints

@router.post("/task/{task_code}")
async def ask_with_task_context(
    task_code: str,
    request: TaskAskRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Ask a question with task-specific context"""
    try:
        service = ContextualQAService(db)
        
        result = await service.ask_with_task_context(
            question=request.question,
            task_code=task_code,
            scope=request.scope,
            top_k=request.top_k
        )
        
        return {
            "success": True,
            "data": result
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/task/{task_code}/context")
async def get_context_preview(
    task_code: str,
    scope: str = Query("self", pattern="^(self|subtasks|tree|inherit)$", description="Context scope"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get preview of context that would be used for Q&A"""
    try:
        service = ContextualQAService(db)
        
        preview = await service.get_context_preview(task_code, scope)
        
        return {
            "success": True,
            "data": preview
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/task/{task_code}/scopes")
async def get_available_scopes(
    task_code: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get available context scopes for a task"""
    try:
        service = ContextualQAService(db)
        
        # Get task to determine available scopes
        from ..services.task_hierarchy_service import TaskHierarchyService
        hierarchy_service = TaskHierarchyService(db)
        
        task = hierarchy_service.get_task_by_code(task_code)
        if not task:
            raise ValidationException(f"Task {task_code} not found")
        
        suggested_scopes = service._get_suggested_scopes(task)
        
        return {
            "success": True,
            "data": {
                "task_code": task_code,
                "task_title": task.title,
                "available_scopes": suggested_scopes
            }
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/explain/scopes")
async def explain_context_scopes(
    api_key: str = Depends(verify_api_key)
):
    """Explain different context scopes"""
    return {
        "success": True,
        "data": {
            "scopes": {
                "self": {
                    "name": "Task hiện tại",
                    "description": "Chỉ sử dụng tài liệu được gán trực tiếp cho task này",
                    "use_when": "Khi bạn muốn hỏi về thông tin cụ thể của task hiện tại",
                    "example": "Trạng thái hiện tại của task này như thế nào?"
                },
                "subtasks": {
                    "name": "Bao gồm subtasks",
                    "description": "Sử dụng tài liệu từ task hiện tại và tất cả subtasks",
                    "use_when": "Khi bạn muốn có overview về toàn bộ công việc trong task và các phần nhỏ",
                    "example": "Tổng quan tiến độ của dự án này như thế nào?"
                },
                "tree": {
                    "name": "Toàn bộ cây phân cấp",
                    "description": "Sử dụng tài liệu từ task hiện tại, parents và tất cả subtasks",
                    "use_when": "Khi bạn cần context đầy đủ của toàn bộ project",
                    "example": "Làm thế nào task này ảnh hưởng đến toàn bộ dự án?"
                },
                "inherit": {
                    "name": "Kế thừa từ parents",
                    "description": "Sử dụng tài liệu từ task hiện tại + tài liệu từ các parent tasks",
                    "use_when": "Khi task hiện tại phụ thuộc vào thông tin từ các task cha",
                    "example": "Dựa trên yêu cầu từ task cha, tôi nên làm gì tiếp theo?"
                }
            },
            "tips": [
                "Bắt đầu với scope 'self' cho câu hỏi cụ thể về task",
                "Sử dụng 'subtasks' khi muốn overview tiến độ",
                "Chọn 'inherit' khi task phụ thuộc vào context từ parent",
                "Dùng 'tree' cho câu hỏi về tác động toàn dự án"
            ]
        }
    }


# Enhanced general ask endpoint with optional task context
@router.post("/enhanced")
async def enhanced_ask(
    request: EnhancedAskRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Enhanced ask endpoint that can use task context or fall back to general Q&A"""
    try:
        if request.task_code:
            # Use contextual Q&A
            service = ContextualQAService(db)
            result = await service.ask_with_task_context(
                question=request.question,
                task_code=request.task_code,
                scope=request.scope,
                top_k=request.top_k
            )
            result["context_type"] = "task_specific"
        else:
            # Fall back to general Q&A
            from .ask import ask_question
            from ..schemas import AskRequest
            
            # Create request object
            ask_request = AskRequest(question=request.question, top_k=request.top_k)
            
            # Use existing general Q&A logic
            result = await ask_question(ask_request, api_key, db)
            
            # Adapt response format
            if isinstance(result, dict) and "data" in result:
                result = result["data"]
            
            result["context_type"] = "general"
            result["task_context"] = None
            result["context_summary"] = {
                "documents_used": len(result.get("refs", [])),
                "task_specific": 0,
                "inherited": 0,
                "general": len(result.get("refs", [])),
                "hierarchy_depth": 0
            }
        
        return {
            "success": True,
            "data": result
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/context/stats")
async def get_context_stats(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get statistics about available context"""
    try:
        from ..services.resource_assignment_service import ResourceAssignmentService
        from ..services.task_hierarchy_service import TaskHierarchyService
        
        resource_service = ResourceAssignmentService(db)
        hierarchy_service = TaskHierarchyService(db)
        
        # Get assignment stats
        assignment_stats = resource_service.get_assignment_stats()
        
        # Get hierarchy stats
        all_tasks = db.query(Task).all()
        root_tasks = [t for t in all_tasks if t.parent_task_id is None]
        max_depth = 0
        
        for task in all_tasks:
            depth = len(task.task_path.split("/")) if task.task_path else 0
            max_depth = max(max_depth, depth)
        
        hierarchy_stats = {
            "total_tasks": len(all_tasks),
            "root_tasks": len(root_tasks),
            "max_hierarchy_depth": max_depth,
            "tasks_with_children": len([t for t in all_tasks if hierarchy_service.get_task_children(t.id)]),
            "leaf_tasks": len([t for t in all_tasks if not hierarchy_service.get_task_children(t.id)])
        }
        
        return {
            "success": True,
            "data": {
                "resource_assignment": assignment_stats,
                "task_hierarchy": hierarchy_stats,
                "context_capabilities": {
                    "scopes_available": ["self", "subtasks", "tree", "inherit"],
                    "max_context_documents": 20,
                    "supports_inheritance": True,
                    "supports_hierarchy": True
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
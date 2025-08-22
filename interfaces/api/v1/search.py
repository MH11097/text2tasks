"""Search API endpoints"""

from fastapi import APIRouter, Query, HTTPException, Depends, Header
from typing import Optional, Dict, Any
import logging

from domain.services.search_service import SearchService
from domain.entities.types import TaskStatus, SourceType
from app.dependencies import container

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize search service
search_service = SearchService(
    task_repository=container.task_repository,
    document_repository=container.document_repository
)

async def verify_api_key_optional(x_api_key: Optional[str] = Header(None)):
    """Optional API key verification for search endpoints"""
    # Search can be public or require API key based on configuration
    # For now, allowing public search access
    return True

@router.get("/search/tasks")
async def search_tasks(
    q: str = Query(..., description="Search query", min_length=1, max_length=200),
    status: Optional[str] = Query(None, regex="^(new|in_progress|blocked|done)$"),
    owner: Optional[str] = Query(None, max_length=100),
    priority: Optional[str] = Query(None, regex="^(low|medium|high|urgent)$"),
    created_by: Optional[str] = Query(None, max_length=100),
    date_from: Optional[str] = Query(None, regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$"),
    date_to: Optional[str] = Query(None, regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$"),
    sort_by: Optional[str] = Query("relevance", regex="^(relevance|created_at|updated_at|title|priority)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    limit: Optional[int] = Query(20, ge=1, le=100),
    api_key: bool = Depends(verify_api_key_optional)
):
    """
    Search tasks with full-text search and advanced filtering
    
    - **q**: Search query (required)
    - **status**: Filter by task status
    - **owner**: Filter by task owner
    - **priority**: Filter by task priority
    - **created_by**: Filter by who created the task
    - **date_from**: Filter tasks created from this date (YYYY-MM-DD)
    - **date_to**: Filter tasks created until this date (YYYY-MM-DD)
    - **sort_by**: Sort results by field (default: relevance)
    - **sort_order**: Sort order (asc/desc)
    - **limit**: Maximum number of results
    """
    try:
        # Build filters
        filters = {}
        if status:
            try:
                filters["status"] = TaskStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status value")
        
        if owner:
            filters["owner"] = owner
        if priority:
            filters["priority"] = priority
        if created_by:
            filters["created_by"] = created_by
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        
        # Perform search
        results = search_service.search_tasks(
            query=q,
            filters=filters if filters else None,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit
        )
        
        logger.info(f"Task search performed", extra={
            "query": q,
            "results_count": len(results.get("results", [])),
            "total_matches": results.get("total", 0),
            "filters": filters
        })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in task search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/search/documents")
async def search_documents(
    q: str = Query(..., description="Search query", min_length=1, max_length=200),
    source_type: Optional[str] = Query(None, regex="^(email|meeting|note|other|document|chat)$"),
    limit: Optional[int] = Query(20, ge=1, le=50),
    api_key: bool = Depends(verify_api_key_optional)
):
    """
    Search documents with full-text search
    
    - **q**: Search query (required)
    - **source_type**: Filter by document source type
    - **limit**: Maximum number of results
    """
    try:
        # Build filters
        filters = {}
        if source_type:
            try:
                filters["source_type"] = SourceType(source_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid source_type value")
        
        # Perform search
        results = search_service.search_documents(
            query=q,
            filters=filters if filters else None,
            limit=limit
        )
        
        logger.info(f"Document search performed", extra={
            "query": q,
            "results_count": len(results.get("results", [])),
            "total_matches": results.get("total", 0),
            "filters": filters
        })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/search")
async def unified_search(
    q: str = Query(..., description="Search query", min_length=1, max_length=200),
    include_tasks: Optional[bool] = Query(True, description="Include tasks in search"),
    include_documents: Optional[bool] = Query(True, description="Include documents in search"),
    status: Optional[str] = Query(None, regex="^(new|in_progress|blocked|done)$"),
    owner: Optional[str] = Query(None, max_length=100),
    priority: Optional[str] = Query(None, regex="^(low|medium|high|urgent)$"),
    source_type: Optional[str] = Query(None, regex="^(email|meeting|note|other|document|chat)$"),
    limit: Optional[int] = Query(30, ge=1, le=100),
    api_key: bool = Depends(verify_api_key_optional)
):
    """
    Unified search across tasks and documents
    
    - **q**: Search query (required)
    - **include_tasks**: Whether to include tasks in search results
    - **include_documents**: Whether to include documents in search results
    - **status**: Filter tasks by status
    - **owner**: Filter tasks by owner
    - **priority**: Filter tasks by priority
    - **source_type**: Filter documents by source type
    - **limit**: Maximum total number of results
    """
    try:
        # Build filters
        filters = {}
        if status:
            try:
                filters["status"] = TaskStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status value")
        
        if owner:
            filters["owner"] = owner
        if priority:
            filters["priority"] = priority
        if source_type:
            try:
                filters["source_type"] = SourceType(source_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid source_type value")
        
        # Perform unified search
        results = search_service.unified_search(
            query=q,
            include_tasks=include_tasks,
            include_documents=include_documents,
            filters=filters if filters else None,
            limit=limit
        )
        
        logger.info(f"Unified search performed", extra={
            "query": q,
            "task_results": len(results.get("tasks", [])),
            "document_results": len(results.get("documents", [])),
            "total_results": results.get("total", 0),
            "include_tasks": include_tasks,
            "include_documents": include_documents,
            "filters": filters
        })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/search/suggestions")
async def get_search_suggestions(
    q: Optional[str] = Query(None, description="Partial query for autocomplete", max_length=100),
    type: Optional[str] = Query("all", regex="^(all|tasks|documents|owners|priorities)$"),
    limit: Optional[int] = Query(10, ge=1, le=20),
    api_key: bool = Depends(verify_api_key_optional)
):
    """
    Get search suggestions and autocomplete options
    
    - **q**: Partial query for autocomplete
    - **type**: Type of suggestions (all, tasks, documents, owners, priorities)
    - **limit**: Maximum number of suggestions
    """
    try:
        suggestions = []
        
        if not q or len(q.strip()) < 2:
            # Return popular search suggestions
            suggestions = [
                "high priority tasks",
                "overdue tasks",
                "recent documents",
                "meeting notes",
                "tasks by John",
                "urgent items",
                "this week",
                "blocked tasks"
            ]
        else:
            # Generate contextual suggestions based on partial query
            query_lower = q.lower().strip()
            
            # Task-related suggestions
            if type in ["all", "tasks"]:
                task_suggestions = [
                    f"{query_lower} high priority",
                    f"{query_lower} status:new",
                    f"{query_lower} overdue",
                    f"tasks about {query_lower}"
                ]
                suggestions.extend(task_suggestions)
            
            # Document-related suggestions
            if type in ["all", "documents"]:
                doc_suggestions = [
                    f"{query_lower} meeting notes",
                    f"{query_lower} documents",
                    f"emails about {query_lower}"
                ]
                suggestions.extend(doc_suggestions)
            
            # Owner/people suggestions
            if type in ["all", "owners"] and len(query_lower) > 2:
                # This could be enhanced with actual user data
                people_suggestions = [
                    f"tasks by {query_lower}",
                    f"{query_lower} assigned tasks"
                ]
                suggestions.extend(people_suggestions)
        
        # Limit and clean suggestions
        final_suggestions = []
        for suggestion in suggestions[:limit]:
            if suggestion and suggestion not in final_suggestions:
                final_suggestions.append(suggestion)
        
        return {
            "suggestions": final_suggestions,
            "query": q,
            "type": type,
            "count": len(final_suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error generating search suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")
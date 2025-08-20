"""
Resource Assignment API Routes
Endpoints for managing resource-task assignments and resource organization.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..database import get_db, Document
from ..services.resource_assignment_service import ResourceAssignmentService
from ..core.exceptions import ValidationException
from ..security import verify_api_key

router = APIRouter(prefix="/resources", tags=["Resource Management"])


# Pydantic models
class ResourceAssignRequest(BaseModel):
    task_ids: List[int] = Field(..., min_items=1)
    assigned_by: Optional[str] = None


class BulkAssignRequest(BaseModel):
    resource_ids: List[int] = Field(..., min_items=1)
    task_id: int


class InheritResourcesRequest(BaseModel):
    assigned_by: Optional[str] = None


# API Endpoints

@router.get("/")
async def get_all_resources(
    assignment_status: Optional[str] = Query(None, pattern="^(unassigned|assigned|archived)$", description="Filter by assignment status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of resources to return"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get all resources with optional status filter"""
    try:
        service = ResourceAssignmentService(db)
        resources = service.get_all_resources(assignment_status, limit)
        
        return {
            "success": True,
            "data": resources,
            "total": len(resources),
            "filter": {
                "assignment_status": assignment_status,
                "limit": limit
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/unassigned")
async def get_unassigned_resources(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of resources to return"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get resources that are not assigned to any task"""
    try:
        service = ResourceAssignmentService(db)
        resources = service.get_unassigned_resources(limit)
        
        return {
            "success": True,
            "data": resources,
            "total": len(resources),
            "message": f"Found {len(resources)} unassigned resources"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{resource_id}/assign")
async def assign_resource_to_tasks(
    resource_id: int,
    request: ResourceAssignRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Assign a resource to multiple tasks"""
    try:
        service = ResourceAssignmentService(db)
        result = service.assign_resource_to_tasks(
            resource_id=resource_id,
            task_ids=request.task_ids,
            assigned_by=request.assigned_by
        )
        
        return {
            "success": True,
            "data": result,
            "message": f"Resource {resource_id} assigned to {result['total_assignments']} tasks"
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{resource_id}/tasks/{task_id}")
async def unassign_resource_from_task(
    resource_id: int,
    task_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Remove assignment between resource and task"""
    try:
        service = ResourceAssignmentService(db)
        success = service.unassign_resource_from_task(resource_id, task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return {
            "success": True,
            "message": f"Resource {resource_id} unassigned from task {task_id}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{resource_id}/tasks")
async def get_resource_tasks(
    resource_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get all tasks assigned to a resource"""
    try:
        service = ResourceAssignmentService(db)
        tasks = service.get_resource_tasks(resource_id)
        
        return {
            "success": True,
            "data": tasks,
            "resource_id": resource_id,
            "total_tasks": len(tasks)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task_resources(
    task_id: int,
    include_inherited: bool = Query(False, description="Include resources inherited from parent tasks"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get all resources assigned to a task"""
    try:
        service = ResourceAssignmentService(db)
        resources = service.get_task_resources(task_id, include_inherited)
        
        return {
            "success": True,
            "data": resources,
            "task_id": task_id,
            "total_resources": len(resources),
            "include_inherited": include_inherited
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/tasks/{task_id}/assign")
async def bulk_assign_resources_to_task(
    task_id: int,
    request: BulkAssignRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Assign multiple resources to a single task"""
    try:
        service = ResourceAssignmentService(db)
        result = service.bulk_assign_resources(
            resource_ids=request.resource_ids,
            task_id=task_id,
            assigned_by=request.assigned_by
        )
        
        return {
            "success": True,
            "data": result,
            "message": f"{result['total_assignments']} resources assigned to task {task_id}"
        }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks/{task_id}/inherited")
async def get_inherited_resources(
    task_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get resources inherited from parent tasks"""
    try:
        service = ResourceAssignmentService(db)
        resources = service.get_inherited_resources(task_id)
        
        return {
            "success": True,
            "data": resources,
            "task_id": task_id,
            "total_inherited": len(resources)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/tasks/{task_id}/inherit")
async def inherit_parent_resources(
    task_id: int,
    request: InheritResourcesRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Inherit all resources from parent tasks"""
    try:
        service = ResourceAssignmentService(db)
        result = service.inherit_parent_resources(task_id, request.assigned_by)
        
        return {
            "success": True,
            "data": result,
            "message": f"Inherited {result['inherited_count']} resources from parent tasks"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/stats")
async def get_assignment_stats(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get assignment statistics"""
    try:
        service = ResourceAssignmentService(db)
        stats = service.get_assignment_stats()
        
        return {
            "success": True,
            "data": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/search")
async def search_resources(
    q: str = Query(..., min_length=3, description="Search query"),
    assignment_status: Optional[str] = Query(None, pattern="^(unassigned|assigned|archived)$"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    limit: int = Query(20, ge=1, le=100),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Search resources by text content"""
    try:
        # Import here to avoid circular imports
        from ..services.document_service import DocumentService
        
        doc_service = DocumentService(db)
        
        # Search documents by similarity
        results = await doc_service.search_documents_by_similarity(q, top_k=limit)
        
        # Filter by assignment status if provided
        if assignment_status or source_type:
            filtered_results = []
            for doc in results:
                doc_obj = db.query(Document).filter(Document.id == doc["id"]).first()
                if doc_obj:
                    if assignment_status and doc_obj.assignment_status != assignment_status:
                        continue
                    if source_type and doc_obj.source_type != source_type:
                        continue
                    filtered_results.append(doc)
            results = filtered_results
        
        return {
            "success": True,
            "data": results,
            "query": q,
            "total": len(results),
            "filters": {
                "assignment_status": assignment_status,
                "source_type": source_type,
                "limit": limit
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/bulk/archive")
async def bulk_archive_resources(
    resource_ids: List[int] = Body(..., min_items=1),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Archive multiple resources"""
    try:
        from ..database import Document
        
        # Update resources to archived status
        updated = db.query(Document).filter(Document.id.in_(resource_ids)).update(
            {Document.assignment_status: "archived"},
            synchronize_session=False
        )
        
        db.commit()
        
        return {
            "success": True,
            "data": {
                "archived_count": updated,
                "resource_ids": resource_ids
            },
            "message": f"Archived {updated} resources"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/bulk/unarchive")
async def bulk_unarchive_resources(
    resource_ids: List[int] = Body(..., min_items=1),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Unarchive multiple resources"""
    try:
        from ..database import Document
        
        # Check which resources have assignments
        service = ResourceAssignmentService(db)
        
        updated_count = 0
        for resource_id in resource_ids:
            tasks = service.get_resource_tasks(resource_id)
            new_status = "assigned" if tasks else "unassigned"
            
            db.query(Document).filter(Document.id == resource_id).update(
                {Document.assignment_status: new_status}
            )
            updated_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "data": {
                "unarchived_count": updated_count,
                "resource_ids": resource_ids
            },
            "message": f"Unarchived {updated_count} resources"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
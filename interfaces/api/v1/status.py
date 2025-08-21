from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from infrastructure.database.connection import get_db_session
from infrastructure.database.models import Task

router = APIRouter()

@router.get("/status")
async def get_status(db: Session = Depends(get_db_session)):
    """Get system status with task counts and summary"""
    
    # Get task counts by status
    status_counts = db.query(
        Task.status,
        func.count(Task.id).label('count')
    ).group_by(Task.status).all()
    
    # Initialize counts
    counts = {
        "new": 0,
        "in_progress": 0,
        "blocked": 0,
        "done": 0
    }
    
    # Update counts from query results
    for status, count in status_counts:
        if status in counts:
            counts[status] = count
    
    # Generate summary text
    total_active = counts["new"] + counts["in_progress"] + counts["blocked"]
    total_tasks = total_active + counts["done"]
    
    if total_tasks == 0:
        summary = "Hệ thống chưa có task nào. Hãy thêm tài liệu để bắt đầu."
    else:
        summary_parts = []
        
        if total_active > 0:
            summary_parts.append(f"Đang có {total_active} task cần xử lý")
            
            if counts["new"] > 0:
                summary_parts.append(f"{counts['new']} task mới")
            if counts["in_progress"] > 0:
                summary_parts.append(f"{counts['in_progress']} đang thực hiện")
            if counts["blocked"] > 0:
                summary_parts.append(f"{counts['blocked']} bị block")
        
        if counts["done"] > 0:
            summary_parts.append(f"{counts['done']} đã hoàn thành")
        
        summary = ". ".join(summary_parts) + "."
        
        # Add recommendations
        if counts["blocked"] > 0:
            summary += " Ưu tiên giải quyết các task bị block."
        elif counts["new"] > 0:
            summary += " Nên bắt đầu với các task mới."
    
    return {
        "summary": summary,
        "counts": counts
    }

@router.get("/resources/stats")
async def get_resource_stats(db: Session = Depends(get_db_session)):
    """Get resource statistics including assignment status and task hierarchy info"""
    from infrastructure.database.models import Document
    
    # Get total documents (acting as resources)
    total_resources = db.query(func.count(Document.id)).scalar()
    
    # Count documents by assignment status (we'll determine this based on if they have tasks)
    assigned_resources = db.query(func.count(Document.id)).filter(
        Document.id.in_(
            db.query(Task.source_doc_id).distinct()
        )
    ).scalar()
    
    unassigned_resources = total_resources - assigned_resources
    
    # Get task hierarchy stats
    total_tasks = db.query(func.count(Task.id)).scalar()
    
    # Count root tasks (assuming tasks without parent are root - this may need adjustment)
    # For now, we'll count all tasks as potentially root since there's no parent_id field visible
    root_tasks = total_tasks  # This may need to be adjusted based on actual hierarchy implementation
    
    # For max hierarchy depth, we'll use 1 as default since hierarchy isn't implemented yet
    max_hierarchy_depth = 1
    
    return {
        "resource_assignment": {
            "total_resources": total_resources,
            "resources_by_status": {
                "assigned": assigned_resources,
                "unassigned": unassigned_resources,
                "archived": 0  # Not implemented yet
            }
        },
        "task_hierarchy": {
            "total_tasks": total_tasks,
            "root_tasks": root_tasks,
            "max_hierarchy_depth": max_hierarchy_depth
        }
    }
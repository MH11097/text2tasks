from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db_session, Task
from ..schemas import StatusResponse, StatusCounts

router = APIRouter()

@router.get("/status", response_model=StatusResponse)
async def get_status(db: Session = Depends(get_db_session)):
    """Get system status with task counts and summary"""
    
    # Get task counts by status
    status_counts = db.query(
        Task.status,
        func.count(Task.id).label('count')
    ).group_by(Task.status).all()
    
    # Initialize counts
    counts = StatusCounts(
        new=0,
        in_progress=0,
        blocked=0,
        done=0
    )
    
    # Update counts from query results
    for status, count in status_counts:
        if status == "new":
            counts.new = count
        elif status == "in_progress":
            counts.in_progress = count
        elif status == "blocked":
            counts.blocked = count
        elif status == "done":
            counts.done = count
    
    # Generate summary text
    total_active = counts.new + counts.in_progress + counts.blocked
    total_tasks = total_active + counts.done
    
    if total_tasks == 0:
        summary = "Hệ thống chưa có task nào. Hãy thêm tài liệu để bắt đầu."
    else:
        summary_parts = []
        
        if total_active > 0:
            summary_parts.append(f"Đang có {total_active} task cần xử lý")
            
            if counts.new > 0:
                summary_parts.append(f"{counts.new} task mới")
            if counts.in_progress > 0:
                summary_parts.append(f"{counts.in_progress} đang thực hiện")
            if counts.blocked > 0:
                summary_parts.append(f"{counts.blocked} bị block")
        
        if counts.done > 0:
            summary_parts.append(f"{counts.done} đã hoàn thành")
        
        summary = ". ".join(summary_parts) + "."
        
        # Add recommendations
        if counts.blocked > 0:
            summary += " Ưu tiên giải quyết các task bị block."
        elif counts.new > 0:
            summary += " Nên bắt đầu với các task mới."
    
    return StatusResponse(
        summary=summary,
        counts=counts
    )
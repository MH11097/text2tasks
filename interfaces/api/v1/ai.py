from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, List, Dict, Any

from domain.services.ai_service import AIService
from domain.services.task_service import TaskService
from domain.entities.exceptions import ValidationException
from shared.config.settings import settings
import logging
from app.dependencies import container

router = APIRouter()
ai_service = AIService(llm_client=container.llm_client)
task_service = TaskService(task_repository=container.task_repository)
logger = logging.getLogger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    from infrastructure.security.security import validate_api_key_header
    validated_key = validate_api_key_header(x_api_key)
    if validated_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return validated_key

@router.post("/ai/generate-tags")
async def generate_task_tags(
    task_id: int,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate smart tags for a task using AI analysis
    """
    try:
        # Get task by ID
        task_dict = task_service.get_task_by_id(task_id)
        if not task_dict:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Convert to TaskEntity (simplified)
        from domain.entities.task import TaskEntity
        task_entity = TaskEntity(
            id=int(task_dict['id']),
            title=task_dict['title'],
            description=task_dict.get('description'),
            status=task_dict['status'],
            priority=task_dict.get('priority', 'medium')
        )
        
        # Generate tags
        tags = ai_service.generate_smart_tags(task_entity)
        
        logger.info(
            "Smart tags generated successfully",
            extra={
                "task_id": task_id,
                "tags_count": len(tags)
            }
        )
        
        return {
            "task_id": task_id,
            "generated_tags": tags,
            "tag_count": len(tags)
        }
        
    except ValidationException as e:
        logger.warning(f"Validation error in tag generation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating tags: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/ai/suggest-related-tasks/{task_id}")
async def suggest_related_tasks(
    task_id: int,
    limit: int = 5
):
    """
    Suggest tasks related to the given task
    """
    try:
        # Get current task
        task_dict = task_service.get_task_by_id(task_id)
        if not task_dict:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get all tasks for comparison
        all_tasks_dict = task_service.get_tasks(limit=1000)
        
        # Convert to TaskEntity objects
        from domain.entities.task import TaskEntity
        
        current_task = TaskEntity(
            id=int(task_dict['id']),
            title=task_dict['title'],
            description=task_dict.get('description'),
            status=task_dict['status']
        )
        
        existing_tasks = []
        for t in all_tasks_dict:
            existing_tasks.append(TaskEntity(
                id=int(t['id']),
                title=t['title'],
                description=t.get('description'),
                status=t['status']
            ))
        
        # Generate suggestions
        suggestions = ai_service.suggest_related_tasks(current_task, existing_tasks)
        
        logger.info(
            "Related tasks suggested successfully",
            extra={
                "task_id": task_id,
                "suggestions_count": len(suggestions)
            }
        )
        
        return {
            "task_id": task_id,
            "related_tasks": suggestions[:limit],
            "total_suggestions": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error suggesting related tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/ai/analyze-dependencies")
async def analyze_task_dependencies(
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze task dependencies and identify critical path
    """
    try:
        # Get all tasks
        all_tasks_dict = task_service.get_tasks(limit=1000)
        
        # Convert to TaskEntity objects
        from domain.entities.task import TaskEntity
        tasks = []
        for t in all_tasks_dict:
            tasks.append(TaskEntity(
                id=int(t['id']),
                title=t['title'],
                description=t.get('description'),
                status=t['status'],
                priority=t.get('priority', 'medium')
            ))
        
        # Analyze dependencies
        analysis = ai_service.analyze_task_dependencies(tasks)
        
        logger.info(
            "Task dependencies analyzed successfully",
            extra={
                "total_tasks": len(tasks),
                "dependencies_found": len(analysis.get('dependencies', []))
            }
        )
        
        return {
            "total_tasks_analyzed": len(tasks),
            "dependencies": analysis.get('dependencies', []),
            "critical_path": analysis.get('critical_path', []),
            "analysis_timestamp": analysis.get('analysis_timestamp')
        }
        
    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/ai/bulk-generate-tags")
async def bulk_generate_tags(
    task_ids: List[int],
    api_key: str = Depends(verify_api_key)
):
    """
    Generate smart tags for multiple tasks in bulk
    """
    try:
        if len(task_ids) > 50:
            raise ValidationException("Maximum 50 tasks allowed for bulk operation")
        
        results = []
        
        for task_id in task_ids:
            try:
                # Get task
                task_dict = task_service.get_task_by_id(task_id)
                if not task_dict:
                    results.append({
                        "task_id": task_id,
                        "success": False,
                        "error": "Task not found"
                    })
                    continue
                
                # Convert to TaskEntity
                from domain.entities.task import TaskEntity
                task_entity = TaskEntity(
                    id=int(task_dict['id']),
                    title=task_dict['title'],
                    description=task_dict.get('description'),
                    status=task_dict['status'],
                    priority=task_dict.get('priority', 'medium')
                )
                
                # Generate tags
                tags = ai_service.generate_smart_tags(task_entity)
                
                results.append({
                    "task_id": task_id,
                    "success": True,
                    "generated_tags": tags,
                    "tag_count": len(tags)
                })
                
            except Exception as e:
                results.append({
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                })
        
        successful_count = sum(1 for r in results if r['success'])
        
        logger.info(
            "Bulk tag generation completed",
            extra={
                "requested_tasks": len(task_ids),
                "successful_tasks": successful_count
            }
        )
        
        return {
            "requested_tasks": len(task_ids),
            "successful_tasks": successful_count,
            "failed_tasks": len(task_ids) - successful_count,
            "results": results
        }
        
    except ValidationException as e:
        logger.warning(f"Validation error in bulk tag generation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in bulk tag generation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/ai/task-insights/{task_id}")
async def get_task_insights(
    task_id: int
):
    """
    Get comprehensive AI insights for a task
    """
    try:
        # Get task
        task_dict = task_service.get_task_by_id(task_id)
        if not task_dict:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Convert to TaskEntity
        from domain.entities.task import TaskEntity
        task_entity = TaskEntity(
            id=int(task_dict['id']),
            title=task_dict['title'],
            description=task_dict.get('description'),
            status=task_dict['status'],
            priority=task_dict.get('priority', 'medium')
        )
        
        # Get all tasks for related analysis
        all_tasks_dict = task_service.get_tasks(limit=1000)
        existing_tasks = []
        for t in all_tasks_dict:
            existing_tasks.append(TaskEntity(
                id=int(t['id']),
                title=t['title'],
                description=t.get('description'),
                status=t['status']
            ))
        
        # Generate insights
        tags = ai_service.generate_smart_tags(task_entity)
        related_tasks = ai_service.suggest_related_tasks(task_entity, existing_tasks)
        
        insights = {
            "task_id": task_id,
            "task_title": task_entity.title,
            "smart_tags": tags,
            "related_tasks": related_tasks[:5],
            "insights": {
                "complexity_score": len(task_entity.description.split()) / 50 if task_entity.description else 0.1,
                "priority_level": task_entity.priority or 'medium',
                "estimated_effort": "high" if len(tags) > 3 else "medium" if len(tags) > 1 else "low"
            }
        }
        
        logger.info(
            "Task insights generated successfully",
            extra={
                "task_id": task_id,
                "tags_count": len(tags),
                "related_tasks_count": len(related_tasks)
            }
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating task insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
"""Task dependencies API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

from domain.services.task_service import TaskService
from app.dependencies import container

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize task service
task_service = TaskService(
    task_repository=container.task_repository
)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """API key verification for dependency endpoints"""
    from infrastructure.security.security import validate_api_key_header
    from shared.config.settings import settings
    
    validated_key = validate_api_key_header(x_api_key)
    if validated_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return validated_key

# Request/Response models
class CreateDependencyRequest(BaseModel):
    dependent_task_id: int = Field(..., description="ID of the task that depends on another")
    prerequisite_task_id: int = Field(..., description="ID of the task that must be completed first")
    dependency_type: str = Field("blocks", pattern="^(blocks|related|subtask)$", description="Type of dependency")
    description: Optional[str] = Field(None, max_length=255, description="Optional description of the dependency")
    created_by: Optional[str] = Field(None, max_length=100, description="Who created the dependency")

class RemoveDependencyRequest(BaseModel):
    dependent_task_id: int = Field(..., description="ID of the dependent task")
    prerequisite_task_id: int = Field(..., description="ID of the prerequisite task")

@router.post("/dependencies")
async def create_dependency(
    request: CreateDependencyRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a dependency between two tasks
    
    - **dependent_task_id**: Task that depends on another
    - **prerequisite_task_id**: Task that must be completed first
    - **dependency_type**: Type of dependency (blocks, related, subtask)
    - **description**: Optional description
    - **created_by**: Who created the dependency
    """
    try:
        success = task_service.task_repository.create_dependency(
            dependent_task_id=request.dependent_task_id,
            prerequisite_task_id=request.prerequisite_task_id,
            dependency_type=request.dependency_type,
            description=request.description,
            created_by=request.created_by
        )
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Failed to create dependency. Check that both tasks exist and dependency doesn't already exist."
            )
        
        logger.info(f"Dependency created", extra={
            "dependent_task_id": request.dependent_task_id,
            "prerequisite_task_id": request.prerequisite_task_id,
            "dependency_type": request.dependency_type
        })
        
        return {
            "message": "Dependency created successfully",
            "dependent_task_id": request.dependent_task_id,
            "prerequisite_task_id": request.prerequisite_task_id,
            "dependency_type": request.dependency_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dependency: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dependency")

@router.delete("/dependencies")
async def remove_dependency(
    request: RemoveDependencyRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Remove a dependency between two tasks
    
    - **dependent_task_id**: ID of the dependent task
    - **prerequisite_task_id**: ID of the prerequisite task
    """
    try:
        success = task_service.task_repository.remove_dependency(
            dependent_task_id=request.dependent_task_id,
            prerequisite_task_id=request.prerequisite_task_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Dependency not found"
            )
        
        logger.info(f"Dependency removed", extra={
            "dependent_task_id": request.dependent_task_id,
            "prerequisite_task_id": request.prerequisite_task_id
        })
        
        return {
            "message": "Dependency removed successfully",
            "dependent_task_id": request.dependent_task_id,
            "prerequisite_task_id": request.prerequisite_task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing dependency: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove dependency")

@router.get("/tasks/{task_id}/dependencies")
async def get_task_dependencies(
    task_id: int,
    api_key: Optional[str] = Header(None)
):
    """
    Get all tasks that this task depends on (prerequisites)
    
    - **task_id**: ID of the task to get dependencies for
    """
    try:
        dependencies = task_service.task_repository.get_task_dependencies(task_id)
        
        logger.info(f"Retrieved task dependencies", extra={
            "task_id": task_id,
            "dependency_count": len(dependencies)
        })
        
        return {
            "task_id": task_id,
            "dependencies": dependencies,
            "count": len(dependencies)
        }
        
    except Exception as e:
        logger.error(f"Error getting task dependencies: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task dependencies")

@router.get("/tasks/{task_id}/dependents")
async def get_dependent_tasks(
    task_id: int,
    api_key: Optional[str] = Header(None)
):
    """
    Get all tasks that depend on this task
    
    - **task_id**: ID of the task to get dependents for
    """
    try:
        dependents = task_service.task_repository.get_dependent_tasks(task_id)
        
        logger.info(f"Retrieved dependent tasks", extra={
            "task_id": task_id,
            "dependent_count": len(dependents)
        })
        
        return {
            "task_id": task_id,
            "dependents": dependents,
            "count": len(dependents)
        }
        
    except Exception as e:
        logger.error(f"Error getting dependent tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dependent tasks")

@router.get("/dependencies/graph")
async def get_dependency_graph(
    task_ids: Optional[str] = None,
    api_key: Optional[str] = Header(None)
):
    """
    Get the complete dependency graph for tasks
    
    - **task_ids**: Optional comma-separated list of task IDs to filter the graph
    """
    try:
        # Parse task_ids if provided
        task_id_list = None
        if task_ids:
            try:
                task_id_list = [int(tid.strip()) for tid in task_ids.split(',')]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid task_ids format. Use comma-separated integers.")
        
        graph = task_service.task_repository.get_dependency_graph(task_id_list)
        
        logger.info(f"Retrieved dependency graph", extra={
            "filtered_task_ids": task_id_list,
            "node_count": len(graph.get("nodes", {})),
            "edge_count": len(graph.get("edges", [])),
            "cycle_count": len(graph.get("cycles", []))
        })
        
        return graph
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dependency graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dependency graph")

@router.get("/dependencies/analysis")
async def analyze_dependencies(
    api_key: Optional[str] = Header(None)
):
    """
    Get detailed analysis of the task dependency structure
    
    Returns insights about the dependency graph including:
    - Critical path analysis
    - Cycle detection
    - Root and leaf tasks
    - Dependency statistics
    """
    try:
        # Get the complete dependency graph
        graph = task_service.task_repository.get_dependency_graph()
        
        # Analyze the graph
        analysis = {
            "summary": {
                "total_nodes": len(graph.get("nodes", {})),
                "total_edges": len(graph.get("edges", [])),
                "root_tasks": len(graph.get("root_tasks", [])),
                "leaf_tasks": len(graph.get("leaf_tasks", [])),
                "cycles_detected": len(graph.get("cycles", []))
            },
            "root_tasks": graph.get("root_tasks", []),
            "leaf_tasks": graph.get("leaf_tasks", []),
            "cycles": graph.get("cycles", []),
            "recommendations": []
        }
        
        # Generate recommendations
        if analysis["summary"]["cycles_detected"] > 0:
            analysis["recommendations"].append({
                "type": "warning",
                "message": f"Found {analysis['summary']['cycles_detected']} circular dependencies that need to be resolved",
                "action": "Review and break circular dependencies to avoid deadlocks"
            })
        
        if analysis["summary"]["root_tasks"] == 0 and analysis["summary"]["total_nodes"] > 0:
            analysis["recommendations"].append({
                "type": "info",
                "message": "All tasks have dependencies - consider if some should be independent starting points",
                "action": "Review task dependencies to identify natural starting points"
            })
        
        if analysis["summary"]["leaf_tasks"] == 0 and analysis["summary"]["total_nodes"] > 0:
            analysis["recommendations"].append({
                "type": "info",
                "message": "All tasks have dependents - consider if this represents a complete workflow",
                "action": "Verify that dependency chain leads to completion"
            })
        
        # Calculate dependency depth
        if graph.get("nodes"):
            max_depth = 0
            for edges in graph.get("edges", []):
                max_depth = max(max_depth, 1)
            analysis["summary"]["max_dependency_depth"] = max_depth
        
        logger.info(f"Dependency analysis completed", extra={
            "total_nodes": analysis["summary"]["total_nodes"],
            "total_edges": analysis["summary"]["total_edges"],
            "cycles": analysis["summary"]["cycles_detected"],
            "recommendations": len(analysis["recommendations"])
        })
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze dependencies")

@router.post("/dependencies/batch")
async def create_batch_dependencies(
    dependencies: List[CreateDependencyRequest],
    api_key: str = Depends(verify_api_key)
):
    """
    Create multiple dependencies in a single request
    
    Useful for setting up complex dependency structures efficiently.
    """
    try:
        results = {
            "created": [],
            "failed": [],
            "total": len(dependencies)
        }
        
        for dep_request in dependencies:
            try:
                success = task_service.task_repository.create_dependency(
                    dependent_task_id=dep_request.dependent_task_id,
                    prerequisite_task_id=dep_request.prerequisite_task_id,
                    dependency_type=dep_request.dependency_type,
                    description=dep_request.description,
                    created_by=dep_request.created_by
                )
                
                if success:
                    results["created"].append({
                        "dependent_task_id": dep_request.dependent_task_id,
                        "prerequisite_task_id": dep_request.prerequisite_task_id,
                        "dependency_type": dep_request.dependency_type
                    })
                else:
                    results["failed"].append({
                        "dependent_task_id": dep_request.dependent_task_id,
                        "prerequisite_task_id": dep_request.prerequisite_task_id,
                        "error": "Failed to create dependency"
                    })
                    
            except Exception as e:
                results["failed"].append({
                    "dependent_task_id": dep_request.dependent_task_id,
                    "prerequisite_task_id": dep_request.prerequisite_task_id,
                    "error": str(e)
                })
        
        logger.info(f"Batch dependency creation completed", extra={
            "total_requested": results["total"],
            "created": len(results["created"]),
            "failed": len(results["failed"])
        })
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch dependency creation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create batch dependencies")
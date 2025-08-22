from fastapi import APIRouter, Depends, HTTPException, Header, File, UploadFile, Form, Query
from fastapi.responses import Response
from typing import Optional, Dict, Any
import logging

from domain.services.export_service import ExportImportService
from domain.entities.exceptions import ValidationException
from shared.config.settings import settings
from app.dependencies import container

router = APIRouter()
export_service = ExportImportService(
    task_repository=container.task_repository,
    document_repository=container.document_repository
)
logger = logging.getLogger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    from infrastructure.security.security import validate_api_key_header
    validated_key = validate_api_key_header(x_api_key)
    if validated_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return validated_key

@router.get("/export/tasks/csv")
async def export_tasks_csv(
    status: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: Optional[int] = Query(1000, le=5000),
    api_key: str = Depends(verify_api_key)
):
    """
    Export tasks to CSV format with optional filtering
    """
    try:
        filters = {}
        if status:
            from domain.entities.types import TaskStatus
            filters['status_filter'] = TaskStatus(status)
        if owner:
            filters['owner_filter'] = owner
        if priority:
            filters['priority_filter'] = priority
        if limit:
            filters['limit'] = limit
        
        csv_content = export_service.export_tasks_csv(filters)
        
        logger.info(
            "Tasks exported to CSV successfully",
            extra={
                "filters": filters,
                "content_length": len(csv_content)
            }
        )
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=tasks_export.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting tasks to CSV: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/export/tasks/json")
async def export_tasks_json(
    status: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: Optional[int] = Query(1000, le=5000),
    api_key: str = Depends(verify_api_key)
):
    """
    Export tasks to JSON format with optional filtering
    """
    try:
        filters = {}
        if status:
            from domain.entities.types import TaskStatus
            filters['status_filter'] = TaskStatus(status)
        if owner:
            filters['owner_filter'] = owner
        if priority:
            filters['priority_filter'] = priority
        if limit:
            filters['limit'] = limit
        
        json_content = export_service.export_tasks_json(filters)
        
        logger.info(
            "Tasks exported to JSON successfully",
            extra={
                "filters": filters,
                "content_length": len(json_content)
            }
        )
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=tasks_export.json"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting tasks to JSON: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/export/documents/csv")
async def export_documents_csv(
    limit: Optional[int] = Query(1000, le=5000),
    api_key: str = Depends(verify_api_key)
):
    """
    Export documents to CSV format
    """
    try:
        csv_content = export_service.export_documents_csv(limit)
        
        logger.info(
            "Documents exported to CSV successfully",
            extra={
                "limit": limit,
                "content_length": len(csv_content)
            }
        )
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=documents_export.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting documents to CSV: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/export/full-backup")
async def export_full_backup(
    api_key: str = Depends(verify_api_key)
):
    """
    Export complete system backup with tasks, documents, and relationships
    """
    try:
        backup_content = export_service.export_full_backup_json()
        
        logger.info(
            "Full backup exported successfully",
            extra={
                "content_length": len(backup_content)
            }
        )
        
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"text2tasks_backup_{timestamp}.json"
        
        return Response(
            content=backup_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error creating full backup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/import/validate")
async def validate_import_data(
    file: UploadFile = File(...),
    format_type: str = Form(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Validate import file before actual import
    """
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Validate data
        validation_result = export_service.validate_import_data(content_str, format_type)
        
        logger.info(
            "Import data validated",
            extra={
                "filename": file.filename,
                "format": format_type,
                "valid": validation_result['valid'],
                "estimated_count": validation_result['estimated_count']
            }
        )
        
        return {
            "filename": file.filename,
            "format": format_type,
            "file_size_bytes": len(content),
            "validation_result": validation_result
        }
        
    except Exception as e:
        logger.error(f"Error validating import data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/import/tasks/csv")
async def import_tasks_csv(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Import tasks from CSV file
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.csv'):
            raise ValidationException("File must be a CSV file")
        
        # Read and process file
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Import tasks
        import_result = export_service.import_tasks_csv(content_str)
        
        logger.info(
            "CSV import completed",
            extra={
                "filename": file.filename,
                "imported_count": import_result['imported_tasks'],
                "failed_count": import_result['failed_tasks']
            }
        )
        
        return {
            "message": "Import completed",
            "filename": file.filename,
            "import_result": import_result
        }
        
    except ValidationException as e:
        logger.warning(f"Validation error in CSV import: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing CSV: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/import/tasks/json")
async def import_tasks_json(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Import tasks from JSON file
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.json'):
            raise ValidationException("File must be a JSON file")
        
        # Read and process file
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Import tasks
        import_result = export_service.import_tasks_json(content_str)
        
        logger.info(
            "JSON import completed",
            extra={
                "filename": file.filename,
                "imported_count": import_result['imported_tasks'],
                "failed_count": import_result['failed_tasks']
            }
        )
        
        return {
            "message": "Import completed",
            "filename": file.filename,
            "import_result": import_result
        }
        
    except ValidationException as e:
        logger.warning(f"Validation error in JSON import: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing JSON: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/export/formats")
async def get_supported_formats():
    """
    Get list of supported export/import formats
    """
    return {
        "export_formats": {
            "csv": {
                "name": "CSV (Comma Separated Values)",
                "description": "Spreadsheet-compatible format",
                "endpoints": ["/export/tasks/csv", "/export/documents/csv"],
                "features": ["filtering", "easy_viewing"]
            },
            "json": {
                "name": "JSON (JavaScript Object Notation)",
                "description": "Structured data format",
                "endpoints": ["/export/tasks/json", "/export/full-backup"],
                "features": ["complete_data", "relationships", "metadata"]
            }
        },
        "import_formats": {
            "csv": {
                "name": "CSV Import",
                "description": "Import tasks from spreadsheet",
                "endpoint": "/import/tasks/csv",
                "required_fields": ["title"],
                "optional_fields": ["description", "status", "priority", "due_date", "owner"]
            },
            "json": {
                "name": "JSON Import", 
                "description": "Import tasks from JSON data",
                "endpoint": "/import/tasks/json",
                "required_fields": ["title"],
                "optional_fields": ["description", "status", "priority", "due_date", "owner"]
            }
        },
        "validation": {
            "endpoint": "/import/validate",
            "description": "Validate import file before processing",
            "supported_formats": ["csv", "json"]
        }
    }

@router.get("/export/stats")
async def get_export_stats(
    api_key: str = Depends(verify_api_key)
):
    """
    Get statistics about exportable data
    """
    try:
        # Get basic counts
        all_tasks = export_service.task_repository.get_tasks(limit=10000)
        all_docs = export_service.document_repository.get_all_documents(limit=10000)
        
        # Count relationships
        relationship_count = 0
        for task in all_tasks[:100]:  # Sample first 100 tasks
            task_id = int(task['id'])
            linked_docs = export_service.task_repository.get_linked_documents(task_id)
            relationship_count += len(linked_docs)
        
        # Estimate total relationships
        if len(all_tasks) > 100:
            relationship_count = int(relationship_count * (len(all_tasks) / 100))
        
        stats = {
            "total_tasks": len(all_tasks),
            "total_documents": len(all_docs),
            "estimated_relationships": relationship_count,
            "export_size_estimates": {
                "tasks_csv_kb": len(all_tasks) * 0.5,  # Rough estimate
                "tasks_json_kb": len(all_tasks) * 1.2,
                "full_backup_kb": (len(all_tasks) * 1.2) + (len(all_docs) * 2.0) + (relationship_count * 0.1)
            },
            "recommended_formats": {
                "small_dataset": "CSV for easy viewing",
                "large_dataset": "JSON for complete data",
                "backup": "Full backup JSON for complete system backup"
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting export stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
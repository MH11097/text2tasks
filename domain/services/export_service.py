"""Export/Import service for tasks and documents"""

import csv
import json
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..entities.task import TaskEntity
from ..entities.document import DocumentEntity
from ..repositories.task_repository import ITaskRepository
from ..repositories.document_repository import IDocumentRepository

logger = logging.getLogger(__name__)

class ExportImportService:
    """Service for exporting and importing data"""
    
    def __init__(self, task_repository: ITaskRepository, document_repository: IDocumentRepository):
        self.task_repository = task_repository
        self.document_repository = document_repository
    
    def export_tasks_csv(self, filters: Dict[str, Any] = None) -> str:
        """Export tasks to CSV format"""
        try:
            # Get tasks with filters
            tasks = self.task_repository.get_tasks(
                status_filter=filters.get('status_filter') if filters else None,
                owner_filter=filters.get('owner_filter') if filters else None,
                priority_filter=filters.get('priority_filter') if filters else None,
                limit=filters.get('limit', 1000) if filters else 1000
            )
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'id', 'title', 'description', 'status', 'priority', 
                'due_date', 'owner', 'created_by', 'source_doc_id',
                'created_at', 'updated_at'
            ])
            
            writer.writeheader()
            for task in tasks:
                writer.writerow(task)
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"Exported {len(tasks)} tasks to CSV")
            return csv_content
            
        except Exception as e:
            logger.error(f"Error exporting tasks to CSV: {e}")
            raise
    
    def export_tasks_json(self, filters: Dict[str, Any] = None) -> str:
        """Export tasks to JSON format"""
        try:
            # Get tasks with filters
            tasks = self.task_repository.get_tasks(
                status_filter=filters.get('status_filter') if filters else None,
                owner_filter=filters.get('owner_filter') if filters else None,
                priority_filter=filters.get('priority_filter') if filters else None,
                limit=filters.get('limit', 1000) if filters else 1000
            )
            
            export_data = {
                'export_timestamp': datetime.utcnow().isoformat(),
                'export_type': 'tasks',
                'total_count': len(tasks),
                'filters_applied': filters or {},
                'data': tasks
            }
            
            json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(tasks)} tasks to JSON")
            return json_content
            
        except Exception as e:
            logger.error(f"Error exporting tasks to JSON: {e}")
            raise
    
    def export_documents_csv(self, limit: int = 1000) -> str:
        """Export documents to CSV format"""
        try:
            # Get documents (assuming we have a method for this)
            documents = self.document_repository.get_all_documents(limit=limit)
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'id', 'text_preview', 'summary', 'source', 'source_type', 'created_at'
            ])
            
            writer.writeheader()
            for doc in documents:
                # Truncate text for CSV
                doc_data = doc.copy()
                if 'text' in doc_data:
                    doc_data['text_preview'] = doc_data['text'][:200] + '...' if len(doc_data['text']) > 200 else doc_data['text']
                    del doc_data['text']  # Remove full text from CSV
                
                writer.writerow(doc_data)
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"Exported {len(documents)} documents to CSV")
            return csv_content
            
        except Exception as e:
            logger.error(f"Error exporting documents to CSV: {e}")
            raise
    
    def export_full_backup_json(self) -> str:
        """Export complete backup with tasks, documents, and relationships"""
        try:
            # Get all tasks
            tasks = self.task_repository.get_tasks(limit=10000)
            
            # Get all documents  
            documents = self.document_repository.get_all_documents(limit=10000)
            
            # Get task-document relationships
            relationships = []
            for task in tasks:
                task_id = int(task['id'])
                linked_docs = self.task_repository.get_linked_documents(task_id)
                for doc in linked_docs:
                    relationships.append({
                        'task_id': task_id,
                        'document_id': doc['id'],
                        'linked_at': doc.get('linked_at'),
                        'created_by': doc.get('created_by')
                    })
            
            backup_data = {
                'backup_timestamp': datetime.utcnow().isoformat(),
                'backup_version': '1.0',
                'system_info': {
                    'tasks_count': len(tasks),
                    'documents_count': len(documents),
                    'relationships_count': len(relationships)
                },
                'tasks': tasks,
                'documents': documents,
                'relationships': relationships
            }
            
            json_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
            
            logger.info(f"Created full backup: {len(tasks)} tasks, {len(documents)} documents, {len(relationships)} relationships")
            return json_content
            
        except Exception as e:
            logger.error(f"Error creating full backup: {e}")
            raise
    
    def import_tasks_csv(self, csv_content: str) -> Dict[str, Any]:
        """Import tasks from CSV content"""
        try:
            # Parse CSV
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            imported_count = 0
            failed_count = 0
            errors = []
            
            for row in reader:
                try:
                    # Create TaskEntity
                    task_entity = TaskEntity(
                        title=row['title'],
                        description=row.get('description'),
                        status=row.get('status', 'new'),
                        priority=row.get('priority', 'medium'),
                        due_date=row.get('due_date'),
                        owner=row.get('owner'),
                        created_by=row.get('created_by', 'import')
                    )
                    
                    # Create task
                    self.task_repository.create(task_entity)
                    imported_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Row {imported_count + failed_count}: {str(e)}")
                    logger.warning(f"Failed to import task: {e}")
            
            result = {
                'imported_tasks': imported_count,
                'failed_tasks': failed_count,
                'total_processed': imported_count + failed_count,
                'errors': errors[:10]  # Limit errors to 10
            }
            
            logger.info(f"Import completed: {imported_count} successful, {failed_count} failed")
            return result
            
        except Exception as e:
            logger.error(f"Error importing tasks from CSV: {e}")
            raise
    
    def import_tasks_json(self, json_content: str) -> Dict[str, Any]:
        """Import tasks from JSON content"""
        try:
            # Parse JSON
            import_data = json.loads(json_content)
            
            # Extract tasks data
            tasks_data = import_data.get('data', []) if 'data' in import_data else import_data
            if not isinstance(tasks_data, list):
                raise ValueError("Invalid JSON format: expected list of tasks")
            
            imported_count = 0
            failed_count = 0
            errors = []
            
            for task_data in tasks_data:
                try:
                    # Create TaskEntity
                    task_entity = TaskEntity(
                        title=task_data['title'],
                        description=task_data.get('description'),
                        status=task_data.get('status', 'new'),
                        priority=task_data.get('priority', 'medium'),
                        due_date=task_data.get('due_date'),
                        owner=task_data.get('owner'),
                        created_by=task_data.get('created_by', 'import')
                    )
                    
                    # Create task
                    self.task_repository.create(task_entity)
                    imported_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Task {imported_count + failed_count}: {str(e)}")
                    logger.warning(f"Failed to import task: {e}")
            
            result = {
                'imported_tasks': imported_count,
                'failed_tasks': failed_count,
                'total_processed': imported_count + failed_count,
                'errors': errors[:10]
            }
            
            logger.info(f"JSON import completed: {imported_count} successful, {failed_count} failed")
            return result
            
        except Exception as e:
            logger.error(f"Error importing tasks from JSON: {e}")
            raise
    
    def validate_import_data(self, content: str, format_type: str) -> Dict[str, Any]:
        """Validate import data before actual import"""
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'preview': [],
                'estimated_count': 0
            }
            
            if format_type.lower() == 'csv':
                csv_file = io.StringIO(content)
                reader = csv.DictReader(csv_file)
                
                required_fields = ['title']
                rows_checked = 0
                
                for row in reader:
                    rows_checked += 1
                    
                    # Check required fields
                    for field in required_fields:
                        if not row.get(field):
                            validation_result['errors'].append(f"Row {rows_checked}: Missing required field '{field}'")
                            validation_result['valid'] = False
                    
                    # Add to preview (first 3 rows)
                    if len(validation_result['preview']) < 3:
                        validation_result['preview'].append({
                            'title': row.get('title', ''),
                            'status': row.get('status', 'new'),
                            'priority': row.get('priority', 'medium')
                        })
                    
                    if rows_checked >= 1000:  # Limit validation to first 1000 rows
                        validation_result['warnings'].append("Only first 1000 rows validated")
                        break
                
                validation_result['estimated_count'] = rows_checked
                
            elif format_type.lower() == 'json':
                import_data = json.loads(content)
                tasks_data = import_data.get('data', []) if 'data' in import_data else import_data
                
                if not isinstance(tasks_data, list):
                    validation_result['errors'].append("Invalid JSON format: expected list of tasks")
                    validation_result['valid'] = False
                    return validation_result
                
                for i, task_data in enumerate(tasks_data[:1000]):  # Check first 1000
                    if not task_data.get('title'):
                        validation_result['errors'].append(f"Task {i+1}: Missing required field 'title'")
                        validation_result['valid'] = False
                    
                    # Add to preview (first 3 tasks)
                    if len(validation_result['preview']) < 3:
                        validation_result['preview'].append({
                            'title': task_data.get('title', ''),
                            'status': task_data.get('status', 'new'),
                            'priority': task_data.get('priority', 'medium')
                        })
                
                validation_result['estimated_count'] = len(tasks_data)
                
                if len(tasks_data) > 1000:
                    validation_result['warnings'].append("Large dataset detected. Import may take longer.")
            
            else:
                validation_result['errors'].append(f"Unsupported format: {format_type}")
                validation_result['valid'] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating import data: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'preview': [],
                'estimated_count': 0
            }
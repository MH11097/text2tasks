"""
Resource Assignment Service
Handles many-to-many relationships between documents (resources) and tasks.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, and_
from datetime import datetime
from ..database import Document, Task, SessionLocal, document_tasks
from ..core.exceptions import ValidationException


class ResourceAssignmentService:
    """Service for managing resource-task assignments"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def assign_resource_to_tasks(
        self, 
        resource_id: int, 
        task_ids: List[int],
        assigned_by: Optional[str] = None,
        inherited: bool = False
    ) -> Dict[str, Any]:
        """Assign a resource to multiple tasks"""
        
        # Verify resource exists
        resource = self.db.query(Document).filter(Document.id == resource_id).first()
        if not resource:
            raise ValidationException(f"Resource {resource_id} not found")
        
        # Verify all tasks exist
        tasks = self.db.query(Task).filter(Task.id.in_(task_ids)).all()
        if len(tasks) != len(task_ids):
            found_ids = [t.id for t in tasks]
            missing_ids = [tid for tid in task_ids if tid not in found_ids]
            raise ValidationException(f"Tasks not found: {missing_ids}")
        
        assignments_created = []
        assignments_skipped = []
        
        for task_id in task_ids:
            # Check if assignment already exists
            existing = self.db.execute(
                text("""
                SELECT 1 FROM document_tasks 
                WHERE document_id = :doc_id AND task_id = :task_id
                """),
                {"doc_id": resource_id, "task_id": task_id}
            ).fetchone()
            
            if existing:
                assignments_skipped.append(task_id)
                continue
            
            # Create assignment
            self.db.execute(
                text("""
                INSERT INTO document_tasks (document_id, task_id, assigned_by, inherited, assigned_at)
                VALUES (:doc_id, :task_id, :assigned_by, :inherited, :assigned_at)
                """),
                {
                    "doc_id": resource_id,
                    "task_id": task_id,
                    "assigned_by": assigned_by,
                    "inherited": inherited,
                    "assigned_at": datetime.utcnow()
                }
            )
            assignments_created.append(task_id)
        
        # Update resource assignment status
        if assignments_created:
            resource.assignment_status = "assigned"
            self.db.commit()
        
        return {
            "resource_id": resource_id,
            "assignments_created": assignments_created,
            "assignments_skipped": assignments_skipped,
            "total_assignments": len(assignments_created)
        }
    
    def unassign_resource_from_task(self, resource_id: int, task_id: int) -> bool:
        """Remove assignment between resource and task"""
        
        result = self.db.execute(
            text("""
            DELETE FROM document_tasks 
            WHERE document_id = :doc_id AND task_id = :task_id
            """),
            {"doc_id": resource_id, "task_id": task_id}
        )
        
        if result.rowcount > 0:
            # Check if resource has any remaining assignments
            remaining = self.db.execute(
                text("SELECT COUNT(*) FROM document_tasks WHERE document_id = :doc_id"),
                {"doc_id": resource_id}
            ).fetchone()
            
            if remaining[0] == 0:
                # Update resource status to unassigned
                resource = self.db.query(Document).filter(Document.id == resource_id).first()
                if resource:
                    resource.assignment_status = "unassigned"
            
            self.db.commit()
            return True
        
        return False
    
    def get_task_resources(
        self, 
        task_id: int, 
        include_inherited: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all resources assigned to a task"""
        
        query = """
        SELECT d.*, dt.assigned_at, dt.assigned_by, dt.inherited
        FROM documents d
        JOIN document_tasks dt ON d.id = dt.document_id
        WHERE dt.task_id = :task_id
        """
        
        if not include_inherited:
            query += " AND dt.inherited = FALSE"
        
        query += " ORDER BY dt.assigned_at DESC"
        
        result = self.db.execute(text(query), {"task_id": task_id}).fetchall()
        
        return [
            {
                "id": row.id,
                "text": row.text[:200] + "..." if len(row.text) > 200 else row.text,
                "source": row.source,
                "source_type": row.source_type,
                "summary": row.summary,
                "assignment_status": row.assignment_status,
                "assigned_at": row.assigned_at.isoformat() if row.assigned_at else None,
                "assigned_by": row.assigned_by,
                "inherited": row.inherited,
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            for row in result
        ]
    
    def get_resource_tasks(self, resource_id: int) -> List[Dict[str, Any]]:
        """Get all tasks assigned to a resource"""
        
        result = self.db.execute(
            text("""
            SELECT t.*, dt.assigned_at, dt.assigned_by, dt.inherited
            FROM tasks t
            JOIN document_tasks dt ON t.id = dt.task_id
            WHERE dt.document_id = :resource_id
            ORDER BY dt.assigned_at DESC
            """),
            {"resource_id": resource_id}
        ).fetchall()
        
        return [
            {
                "id": row.id,
                "title": row.title,
                "task_code": row.task_code,
                "status": row.status,
                "priority": row.priority,
                "progress_percentage": row.progress_percentage,
                "due_date": row.due_date,
                "owner": row.owner,
                "task_level": row.task_level,
                "assigned_at": row.assigned_at.isoformat() if row.assigned_at else None,
                "assigned_by": row.assigned_by,
                "inherited": row.inherited
            }
            for row in result
        ]
    
    def get_unassigned_resources(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get resources that are not assigned to any task"""
        
        resources = self.db.query(Document).filter(
            Document.assignment_status == "unassigned"
        ).limit(limit).all()
        
        return [
            {
                "id": resource.id,
                "text": resource.text[:200] + "..." if len(resource.text) > 200 else resource.text,
                "source": resource.source,
                "source_type": resource.source_type,
                "summary": resource.summary,
                "assignment_status": resource.assignment_status,
                "created_at": resource.created_at.isoformat() if resource.created_at else None
            }
            for resource in resources
        ]
    
    def get_all_resources(
        self, 
        assignment_status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all resources with optional status filter"""
        
        query = self.db.query(Document)
        
        if assignment_status:
            query = query.filter(Document.assignment_status == assignment_status)
        
        resources = query.order_by(Document.created_at.desc()).limit(limit).all()
        
        # Get task counts for each resource
        result = []
        for resource in resources:
            task_count = self.db.execute(
                text("SELECT COUNT(*) FROM document_tasks WHERE document_id = :doc_id"),
                {"doc_id": resource.id}
            ).fetchone()[0]
            
            result.append({
                "id": resource.id,
                "text": resource.text[:200] + "..." if len(resource.text) > 200 else resource.text,
                "source": resource.source,
                "source_type": resource.source_type,
                "summary": resource.summary,
                "assignment_status": resource.assignment_status,
                "task_count": task_count,
                "created_at": resource.created_at.isoformat() if resource.created_at else None
            })
        
        return result
    
    def bulk_assign_resources(
        self, 
        resource_ids: List[int], 
        task_id: int,
        assigned_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assign multiple resources to a single task"""
        
        # Verify task exists
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValidationException(f"Task {task_id} not found")
        
        # Verify all resources exist
        resources = self.db.query(Document).filter(Document.id.in_(resource_ids)).all()
        if len(resources) != len(resource_ids):
            found_ids = [r.id for r in resources]
            missing_ids = [rid for rid in resource_ids if rid not in found_ids]
            raise ValidationException(f"Resources not found: {missing_ids}")
        
        assignments_created = []
        assignments_skipped = []
        
        for resource_id in resource_ids:
            # Check if assignment already exists
            existing = self.db.execute(
                text("""
                SELECT 1 FROM document_tasks 
                WHERE document_id = :doc_id AND task_id = :task_id
                """),
                {"doc_id": resource_id, "task_id": task_id}
            ).fetchone()
            
            if existing:
                assignments_skipped.append(resource_id)
                continue
            
            # Create assignment
            self.db.execute(
                text("""
                INSERT INTO document_tasks (document_id, task_id, assigned_by, inherited, assigned_at)
                VALUES (:doc_id, :task_id, :assigned_by, :inherited, :assigned_at)
                """),
                {
                    "doc_id": resource_id,
                    "task_id": task_id,
                    "assigned_by": assigned_by,
                    "inherited": False,
                    "assigned_at": datetime.utcnow()
                }
            )
            assignments_created.append(resource_id)
        
        # Update resources assignment status
        if assignments_created:
            self.db.execute(
                text("""
                UPDATE documents 
                SET assignment_status = 'assigned' 
                WHERE id IN :resource_ids
                """),
                {"resource_ids": tuple(assignments_created)}
            )
            self.db.commit()
        
        return {
            "task_id": task_id,
            "assignments_created": assignments_created,
            "assignments_skipped": assignments_skipped,
            "total_assignments": len(assignments_created)
        }
    
    def get_inherited_resources(self, task_id: int) -> List[Dict[str, Any]]:
        """Get resources inherited from parent tasks"""
        from .task_hierarchy_service import TaskHierarchyService
        
        hierarchy_service = TaskHierarchyService(self.db)
        ancestors = hierarchy_service.get_task_ancestors(task_id)
        
        if not ancestors:
            return []
        
        ancestor_ids = [a.id for a in ancestors]
        
        result = self.db.execute(
            text("""
            SELECT DISTINCT d.*, dt.assigned_at, dt.assigned_by, t.task_code as source_task_code
            FROM documents d
            JOIN document_tasks dt ON d.id = dt.document_id
            JOIN tasks t ON dt.task_id = t.id
            WHERE dt.task_id IN :ancestor_ids
            AND dt.inherited = FALSE
            ORDER BY dt.assigned_at DESC
            """),
            {"ancestor_ids": tuple(ancestor_ids)}
        ).fetchall()
        
        return [
            {
                "id": row.id,
                "text": row.text[:200] + "..." if len(row.text) > 200 else row.text,
                "source": row.source,
                "source_type": row.source_type,
                "summary": row.summary,
                "source_task_code": row.source_task_code,
                "assigned_at": row.assigned_at.isoformat() if row.assigned_at else None,
                "assigned_by": row.assigned_by
            }
            for row in result
        ]
    
    def inherit_parent_resources(self, task_id: int, assigned_by: Optional[str] = None) -> Dict[str, Any]:
        """Inherit all resources from parent tasks"""
        inherited_resources = self.get_inherited_resources(task_id)
        
        if not inherited_resources:
            return {
                "task_id": task_id,
                "inherited_count": 0,
                "inherited_resources": []
            }
        
        assignments_created = []
        
        for resource in inherited_resources:
            # Check if assignment already exists
            existing = self.db.execute(
                text("""
                SELECT 1 FROM document_tasks 
                WHERE document_id = :doc_id AND task_id = :task_id
                """),
                {"doc_id": resource["id"], "task_id": task_id}
            ).fetchone()
            
            if not existing:
                # Create inherited assignment
                self.db.execute(
                    text("""
                    INSERT INTO document_tasks (document_id, task_id, assigned_by, inherited, assigned_at)
                    VALUES (:doc_id, :task_id, :assigned_by, :inherited, :assigned_at)
                    """),
                    {
                        "doc_id": resource["id"],
                        "task_id": task_id,
                        "assigned_by": assigned_by or "auto-inherit",
                        "inherited": True,
                        "assigned_at": datetime.utcnow()
                    }
                )
                assignments_created.append(resource["id"])
        
        if assignments_created:
            self.db.commit()
        
        return {
            "task_id": task_id,
            "inherited_count": len(assignments_created),
            "inherited_resources": [r for r in inherited_resources if r["id"] in assignments_created]
        }
    
    def get_assignment_stats(self) -> Dict[str, Any]:
        """Get assignment statistics"""
        
        stats = {}
        
        # Total resources
        stats["total_resources"] = self.db.query(Document).count()
        
        # Resources by status
        status_stats = self.db.execute(
            text("SELECT assignment_status, COUNT(*) FROM documents GROUP BY assignment_status")
        ).fetchall()
        
        stats["resources_by_status"] = {
            row[0]: row[1] for row in status_stats
        }
        
        # Total tasks
        stats["total_tasks"] = self.db.query(Task).count()
        
        # Tasks with resources
        tasks_with_resources = self.db.execute(
            text("SELECT COUNT(DISTINCT task_id) FROM document_tasks")
        ).fetchone()[0]
        
        stats["tasks_with_resources"] = tasks_with_resources
        stats["tasks_without_resources"] = stats["total_tasks"] - tasks_with_resources
        
        # Total assignments
        stats["total_assignments"] = self.db.execute(
            text("SELECT COUNT(*) FROM document_tasks")
        ).fetchone()[0]
        
        # Inherited vs direct assignments
        inherited_stats = self.db.execute(
            text("SELECT inherited, COUNT(*) FROM document_tasks GROUP BY inherited")
        ).fetchall()
        
        stats["assignments_by_type"] = {
            "inherited" if row[0] else "direct": row[1] for row in inherited_stats
        }
        
        return stats
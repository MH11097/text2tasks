"""
Contextual Q&A Service
Advanced Q&A system that builds context based on task scope and hierarchy.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import Document, Task, SessionLocal
from ..core.exceptions import ValidationException
from .task_hierarchy_service import TaskHierarchyService
from .resource_assignment_service import ResourceAssignmentService
from .document_service import DocumentService


class ContextualQAService:
    """Service for context-aware question answering"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.hierarchy_service = TaskHierarchyService(self.db)
        self.resource_service = ResourceAssignmentService(self.db)
        self.document_service = DocumentService(self.db)
    
    async def ask_with_task_context(
        self,
        question: str,
        task_code: str,
        scope: str = "self",
        top_k: int = 6
    ) -> Dict[str, Any]:
        """
        Ask a question with task-specific context
        
        Args:
            question: The question to ask
            task_code: Task code to provide context
            scope: Context scope (self|subtasks|tree|inherit)
            top_k: Maximum number of context documents
        """
        
        # Get task
        task = self.hierarchy_service.get_task_by_code(task_code)
        if not task:
            raise ValidationException(f"Task {task_code} not found")
        
        # Build context based on scope
        context_data = await self._build_context_by_scope(task, scope, question, top_k)
        
        # Generate answer using LLM
        from ..llm_client import llm_client
        
        # Build context string
        context_parts = []
        
        # Add task information
        if context_data["task_info"]:
            context_parts.append("📋 THÔNG TIN TASK:")
            context_parts.append(f"- Task: {task.title} ({task.task_code})")
            if task.description:
                context_parts.append(f"- Mô tả: {task.description}")
            context_parts.append(f"- Trạng thái: {task.status} | Độ ưu tiên: {task.priority}")
            if task.progress_percentage:
                context_parts.append(f"- Tiến độ: {task.progress_percentage}%")
            if task.owner:
                context_parts.append(f"- Người phụ trách: {task.owner}")
            if task.due_date:
                context_parts.append(f"- Hạn chót: {task.due_date}")
            context_parts.append("")
        
        # Add hierarchy context
        if context_data["hierarchy_context"]:
            context_parts.append("🌳 BỐI CẢNH PHÂN CẤP:")
            
            if context_data["hierarchy_context"]["ancestors"]:
                context_parts.append("- Parent Tasks:")
                for ancestor in context_data["hierarchy_context"]["ancestors"][-2:]:  # Last 2 ancestors
                    context_parts.append(f"  • {ancestor['title']} ({ancestor['task_code']})")
            
            if context_data["hierarchy_context"]["children"] and scope in ["subtasks", "tree"]:
                context_parts.append("- Subtasks:")
                for child in context_data["hierarchy_context"]["children"][:5]:  # First 5 children
                    status_emoji = "✅" if child["status"] == "done" else "🔄" if child["status"] == "in_progress" else "📋"
                    context_parts.append(f"  • {status_emoji} {child['title']} ({child['task_code']}) - {child['progress_percentage']}%")
            
            context_parts.append("")
        
        # Add relevant documents
        if context_data["documents"]:
            context_parts.append("📚 TÀI LIỆU LIÊN QUAN:")
            
            # Task-specific resources (highest priority)
            task_docs = [doc for doc in context_data["documents"] if doc.get("source") == "task"]
            if task_docs:
                context_parts.append("- Tài liệu của task:")
                for doc in task_docs[:3]:
                    context_parts.append(f"  • {doc['summary'] or doc['text'][:100]}...")
            
            # Inherited resources (medium priority)  
            inherited_docs = [doc for doc in context_data["documents"] if doc.get("source") == "inherited"]
            if inherited_docs and scope == "inherit":
                context_parts.append("- Tài liệu từ parent tasks:")
                for doc in inherited_docs[:2]:
                    context_parts.append(f"  • {doc['summary'] or doc['text'][:100]}...")
            
            # General relevant documents (lower priority)
            general_docs = [doc for doc in context_data["documents"] if doc.get("source") == "general"]
            if general_docs:
                context_parts.append("- Tài liệu chung liên quan:")
                for doc in general_docs[:2]:
                    similarity = doc.get("similarity", 0)
                    context_parts.append(f"  • {doc['summary'] or doc['text'][:100]}... (similarity: {similarity:.2f})")
            
            context_parts.append("")
        
        # Add related tasks from other contexts (if scope is tree)
        if scope == "tree" and context_data.get("related_tasks"):
            context_parts.append("🔗 TASKS LIÊN QUAN:")
            for related_task in context_data["related_tasks"][:3]:
                context_parts.append(f"- {related_task['title']} ({related_task['task_code']}) - {related_task['status']}")
            context_parts.append("")
        
        context_string = "\n".join(context_parts)
        
        # Generate answer
        answer_result = await llm_client.answer_question(question, context_string)
        
        # Extract relevant document IDs for references
        doc_refs = []
        if context_data["documents"]:
            doc_refs = [str(doc["id"]) for doc in context_data["documents"][:5]]
        
        return {
            "answer": answer_result.get("answer", "Không thể tạo câu trả lời."),
            "task_context": {
                "task_code": task_code,
                "task_title": task.title,
                "scope": scope
            },
            "context_summary": {
                "documents_used": len(context_data["documents"]),
                "task_specific": len([d for d in context_data["documents"] if d.get("source") == "task"]),
                "inherited": len([d for d in context_data["documents"] if d.get("source") == "inherited"]),
                "general": len([d for d in context_data["documents"] if d.get("source") == "general"]),
                "hierarchy_depth": len(context_data["hierarchy_context"].get("ancestors", [])) if context_data["hierarchy_context"] else 0
            },
            "refs": doc_refs,
            "suggested_next_steps": answer_result.get("suggested_next_steps", [])
        }
    
    async def _build_context_by_scope(
        self,
        task: Task,
        scope: str,
        question: str,
        top_k: int
    ) -> Dict[str, Any]:
        """Build context based on the specified scope"""
        
        context_data = {
            "task_info": True,
            "hierarchy_context": None,
            "documents": [],
            "related_tasks": []
        }
        
        if scope == "self":
            # Only current task resources
            resources = self.resource_service.get_task_resources(task.id, include_inherited=False)
            context_data["documents"] = [
                {
                    **doc,
                    "source": "task",
                    "similarity": 1.0  # Perfect match for task-specific resources
                }
                for doc in resources[:top_k//2]
            ]
            
            # Add some general documents if we have space
            if len(context_data["documents"]) < top_k:
                remaining = top_k - len(context_data["documents"])
                general_docs = await self.document_service.search_documents_by_similarity(
                    question, top_k=remaining
                )
                context_data["documents"].extend([
                    {**doc, "source": "general"}
                    for doc in general_docs[:remaining]
                ])
        
        elif scope == "subtasks":
            # Current task + subtasks resources
            children = self.hierarchy_service.get_task_children(task.id)
            context_data["hierarchy_context"] = {
                "ancestors": [],
                "children": [
                    {
                        "id": child.id,
                        "title": child.title,
                        "task_code": child.task_code,
                        "status": child.status,
                        "progress_percentage": child.progress_percentage or 0
                    }
                    for child in children
                ]
            }
            
            # Get resources from current task and children
            all_task_ids = [task.id] + [child.id for child in children]
            all_resources = []
            
            for task_id in all_task_ids:
                task_resources = self.resource_service.get_task_resources(task_id, include_inherited=False)
                for res in task_resources:
                    res["source"] = "task"
                    res["similarity"] = 1.0
                all_resources.extend(task_resources)
            
            # Remove duplicates and limit
            seen_ids = set()
            unique_resources = []
            for res in all_resources:
                if res["id"] not in seen_ids:
                    unique_resources.append(res)
                    seen_ids.add(res["id"])
            
            context_data["documents"] = unique_resources[:top_k]
        
        elif scope == "tree":
            # Full task tree context
            ancestors = self.hierarchy_service.get_task_ancestors(task.id)
            descendants = self.hierarchy_service.get_task_descendants(task.id)
            
            context_data["hierarchy_context"] = {
                "ancestors": [
                    {
                        "id": ancestor.id,
                        "title": ancestor.title,
                        "task_code": ancestor.task_code,
                        "task_level": ancestor.task_level
                    }
                    for ancestor in ancestors
                ],
                "children": [
                    {
                        "id": desc.id,
                        "title": desc.title,
                        "task_code": desc.task_code,
                        "status": desc.status,
                        "progress_percentage": desc.progress_percentage or 0,
                        "task_level": desc.task_level
                    }
                    for desc in descendants[:10]  # Limit descendants
                ]
            }
            
            # Get resources from entire tree
            all_task_ids = [task.id] + [a.id for a in ancestors] + [d.id for d in descendants]
            all_resources = []
            
            for task_id in all_task_ids:
                task_resources = self.resource_service.get_task_resources(task_id, include_inherited=False)
                for res in task_resources:
                    res["source"] = "task"
                    res["similarity"] = 1.0
                all_resources.extend(task_resources)
            
            # Remove duplicates and prioritize by task level (closer = higher priority)
            seen_ids = set()
            unique_resources = []
            
            # First add current task resources
            current_resources = self.resource_service.get_task_resources(task.id, include_inherited=False)
            for res in current_resources:
                if res["id"] not in seen_ids:
                    res["source"] = "task"
                    res["similarity"] = 1.0
                    unique_resources.append(res)
                    seen_ids.add(res["id"])
            
            # Then add ancestor resources (reverse order - closer ancestors first)
            for ancestor in reversed(ancestors):
                ancestor_resources = self.resource_service.get_task_resources(ancestor.id, include_inherited=False)
                for res in ancestor_resources:
                    if res["id"] not in seen_ids and len(unique_resources) < top_k:
                        res["source"] = "task"
                        res["similarity"] = 0.9
                        unique_resources.append(res)
                        seen_ids.add(res["id"])
            
            # Finally add descendant resources
            for desc in descendants:
                if len(unique_resources) >= top_k:
                    break
                desc_resources = self.resource_service.get_task_resources(desc.id, include_inherited=False)
                for res in desc_resources:
                    if res["id"] not in seen_ids and len(unique_resources) < top_k:
                        res["source"] = "task"
                        res["similarity"] = 0.8
                        unique_resources.append(res)
                        seen_ids.add(res["id"])
            
            context_data["documents"] = unique_resources[:top_k]
            
            # Add related tasks info
            context_data["related_tasks"] = [
                {
                    "id": desc.id,
                    "title": desc.title,
                    "task_code": desc.task_code,
                    "status": desc.status,
                    "task_level": desc.task_level
                }
                for desc in descendants[:5]
            ]
        
        elif scope == "inherit":
            # Current task + inherited resources from parents
            current_resources = self.resource_service.get_task_resources(task.id, include_inherited=False)
            inherited_resources = self.resource_service.get_inherited_resources(task.id)
            
            ancestors = self.hierarchy_service.get_task_ancestors(task.id)
            context_data["hierarchy_context"] = {
                "ancestors": [
                    {
                        "id": ancestor.id,
                        "title": ancestor.title,
                        "task_code": ancestor.task_code,
                        "task_level": ancestor.task_level
                    }
                    for ancestor in ancestors
                ],
                "children": []
            }
            
            # Combine resources with priority
            all_docs = []
            
            # Task-specific resources (highest priority)
            for res in current_resources:
                res["source"] = "task"
                res["similarity"] = 1.0
                all_docs.append(res)
            
            # Inherited resources (medium priority)
            for res in inherited_resources:
                res["source"] = "inherited"
                res["similarity"] = 0.9
                all_docs.append(res)
            
            # Fill remaining with general documents
            if len(all_docs) < top_k:
                remaining = top_k - len(all_docs)
                general_docs = await self.document_service.search_documents_by_similarity(
                    question, top_k=remaining
                )
                for doc in general_docs:
                    # Skip if already included
                    if not any(d["id"] == doc["id"] for d in all_docs):
                        doc["source"] = "general"
                        all_docs.append(doc)
            
            context_data["documents"] = all_docs[:top_k]
        
        else:
            raise ValidationException(f"Invalid scope: {scope}. Must be one of: self, subtasks, tree, inherit")
        
        return context_data
    
    async def get_context_preview(
        self,
        task_code: str,
        scope: str = "self"
    ) -> Dict[str, Any]:
        """Get a preview of context that would be used for Q&A without asking a question"""
        
        task = self.hierarchy_service.get_task_by_code(task_code)
        if not task:
            raise ValidationException(f"Task {task_code} not found")
        
        # Build context with a dummy question
        context_data = await self._build_context_by_scope(task, scope, "preview", 6)
        
        return {
            "task": {
                "id": task.id,
                "title": task.title,
                "task_code": task.task_code,
                "status": task.status,
                "progress_percentage": task.progress_percentage,
                "description": task.description
            },
            "scope": scope,
            "available_resources": {
                "task_specific": len([d for d in context_data["documents"] if d.get("source") == "task"]),
                "inherited": len([d for d in context_data["documents"] if d.get("source") == "inherited"]),
                "general": len([d for d in context_data["documents"] if d.get("source") == "general"]),
                "total": len(context_data["documents"])
            },
            "hierarchy_context": context_data["hierarchy_context"],
            "suggested_scopes": self._get_suggested_scopes(task)
        }
    
    def _get_suggested_scopes(self, task: Task) -> List[Dict[str, Any]]:
        """Get suggested scopes based on task hierarchy"""
        scopes = [
            {
                "scope": "self",
                "name": "Chỉ task này",
                "description": "Chỉ sử dụng tài liệu của task hiện tại"
            }
        ]
        
        # Check if has children
        children = self.hierarchy_service.get_task_children(task.id)
        if children:
            scopes.append({
                "scope": "subtasks",
                "name": "Bao gồm subtasks",
                "description": f"Task hiện tại + {len(children)} subtasks"
            })
        
        # Check if has ancestors
        ancestors = self.hierarchy_service.get_task_ancestors(task.id)
        if ancestors:
            scopes.append({
                "scope": "inherit",
                "name": "Kế thừa từ parent",
                "description": f"Bao gồm tài liệu từ {len(ancestors)} parent tasks"
            })
        
        # Always suggest tree if part of hierarchy
        if ancestors or children:
            scopes.append({
                "scope": "tree",
                "name": "Toàn bộ project",
                "description": "Tất cả tasks trong cây phân cấp"
            })
        
        return scopes
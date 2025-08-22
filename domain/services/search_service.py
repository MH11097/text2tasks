"""Advanced search service for tasks and documents"""

from typing import List, Dict, Any, Optional, Tuple
import re
from datetime import datetime, date
import logging

from ..repositories.task_repository import ITaskRepository
from ..repositories.document_repository import IDocumentRepository
from ..entities.task import TaskEntity
from ..entities.types import TaskStatus, SourceType

logger = logging.getLogger(__name__)

class SearchService:
    """Advanced search service with full-text search and filtering"""
    
    def __init__(self, task_repository: ITaskRepository, document_repository: IDocumentRepository):
        self.task_repository = task_repository
        self.document_repository = document_repository
    
    def search_tasks(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Advanced task search with full-text search and filtering"""
        try:
            # Get all tasks with basic filters
            all_tasks = self.task_repository.get_tasks(
                status_filter=filters.get("status") if filters else None,
                owner_filter=filters.get("owner") if filters else None,
                priority_filter=filters.get("priority") if filters else None,
                created_by_filter=filters.get("created_by") if filters else None,
                limit=1000  # Get more for search scoring
            )
            
            # Apply text search and scoring
            scored_tasks = []
            search_terms = self._extract_search_terms(query)
            
            for task in all_tasks:
                score = self._calculate_task_relevance_score(task, search_terms, query)
                if score > 0:
                    task_with_score = task.copy()
                    task_with_score["relevance_score"] = score
                    scored_tasks.append(task_with_score)
            
            # Apply date range filters if provided
            if filters:
                scored_tasks = self._apply_date_filters(scored_tasks, filters)
            
            # Sort results
            if sort_by == "relevance":
                scored_tasks.sort(key=lambda x: x["relevance_score"], reverse=(sort_order == "desc"))
            else:
                # Default sorting by other fields
                scored_tasks.sort(key=lambda x: x.get(sort_by, ""), reverse=(sort_order == "desc"))
            
            # Apply limit
            results = scored_tasks[:limit]
            
            # Generate search suggestions
            suggestions = self._generate_search_suggestions(query, search_terms, len(results))
            
            return {
                "results": results,
                "total": len(scored_tasks),
                "query": query,
                "suggestions": suggestions,
                "filters_applied": filters or {},
                "search_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in task search: {e}")
            return {
                "results": [],
                "total": 0,
                "query": query,
                "error": "Search failed",
                "suggestions": []
            }
    
    def search_documents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search documents with full-text search"""
        try:
            # Get all documents with basic filters
            all_documents = self.document_repository.get_documents(
                source_type=filters.get("source_type") if filters else None,
                limit=1000
            )
            
            # Apply text search and scoring
            scored_documents = []
            search_terms = self._extract_search_terms(query)
            
            for doc in all_documents:
                score = self._calculate_document_relevance_score(doc, search_terms, query)
                if score > 0:
                    doc_with_score = doc.copy()
                    doc_with_score["relevance_score"] = score
                    # Add snippet for preview
                    doc_with_score["snippet"] = self._generate_document_snippet(doc, search_terms)
                    scored_documents.append(doc_with_score)
            
            # Sort by relevance
            scored_documents.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Apply limit
            results = scored_documents[:limit]
            
            return {
                "results": results,
                "total": len(scored_documents),
                "query": query,
                "search_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in document search: {e}")
            return {
                "results": [],
                "total": 0,
                "query": query,
                "error": "Search failed"
            }
    
    def unified_search(
        self,
        query: str,
        include_tasks: bool = True,
        include_documents: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 30
    ) -> Dict[str, Any]:
        """Unified search across tasks and documents"""
        results = {
            "tasks": [],
            "documents": [],
            "total": 0,
            "query": query,
            "search_timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if include_tasks:
                task_results = self.search_tasks(query, filters, limit=limit//2 if include_documents else limit)
                results["tasks"] = task_results["results"]
                results["task_suggestions"] = task_results.get("suggestions", [])
            
            if include_documents:
                doc_results = self.search_documents(query, filters, limit=limit//2 if include_tasks else limit)
                results["documents"] = doc_results["results"]
            
            results["total"] = len(results["tasks"]) + len(results["documents"])
            
            # Cross-reference related items
            results["related_items"] = self._find_cross_references(results["tasks"], results["documents"])
            
            return results
            
        except Exception as e:
            logger.error(f"Error in unified search: {e}")
            results["error"] = "Search failed"
            return results
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract meaningful search terms from query"""
        # Remove common words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        # Extract words and phrases
        terms = []
        words = re.findall(r'\b\w{2,}\b', query.lower())
        
        # Add individual meaningful words
        for word in words:
            if word not in stop_words and len(word) > 2:
                terms.append(word)
        
        # Add quoted phrases
        phrases = re.findall(r'"([^"]*)"', query)
        for phrase in phrases:
            if phrase.strip():
                terms.append(phrase.strip().lower())
        
        return terms
    
    def _calculate_task_relevance_score(self, task: Dict[str, Any], search_terms: List[str], original_query: str) -> float:
        """Calculate relevance score for a task"""
        score = 0.0
        
        # Combine all searchable text
        searchable_text = f"{task.get('title', '')} {task.get('description', '')}".lower()
        
        # Exact phrase matches get highest score
        if original_query.lower() in searchable_text:
            score += 10.0
        
        # Individual term matches
        for term in search_terms:
            # Title matches are more important
            title_matches = len(re.findall(re.escape(term), task.get('title', '').lower()))
            score += title_matches * 3.0
            
            # Description matches
            description_matches = len(re.findall(re.escape(term), task.get('description', '').lower()))
            score += description_matches * 1.5
            
            # Owner/creator matches
            if term in task.get('owner', '').lower():
                score += 2.0
            if term in task.get('created_by', '').lower():
                score += 1.5
        
        # Boost score for recent tasks
        try:
            if task.get('created_at'):
                created_date = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                days_old = (datetime.utcnow().replace(tzinfo=created_date.tzinfo) - created_date).days
                if days_old < 7:
                    score *= 1.2  # 20% boost for tasks from last week
                elif days_old < 30:
                    score *= 1.1  # 10% boost for tasks from last month
        except (ValueError, TypeError):
            pass
        
        # Boost urgent/high priority tasks
        priority = task.get('priority', '').lower()
        if priority in ['urgent', 'high']:
            score *= 1.15
        
        return score
    
    def _calculate_document_relevance_score(self, document: Dict[str, Any], search_terms: List[str], original_query: str) -> float:
        """Calculate relevance score for a document"""
        score = 0.0
        
        # Combine all searchable text
        searchable_text = f"{document.get('text', '')} {document.get('summary', '')}".lower()
        
        # Exact phrase matches get highest score
        if original_query.lower() in searchable_text:
            score += 15.0  # Documents get higher exact match score
        
        # Individual term matches
        for term in search_terms:
            # Summary matches are most important
            summary_matches = len(re.findall(re.escape(term), document.get('summary', '').lower()))
            score += summary_matches * 4.0
            
            # Text content matches
            text_matches = len(re.findall(re.escape(term), document.get('text', '').lower()))
            score += min(text_matches, 10) * 1.0  # Cap text matches to avoid over-weighting
            
            # Source matches
            if term in document.get('source', '').lower():
                score += 2.0
        
        return score
    
    def _apply_date_filters(self, tasks: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply date range filters to tasks"""
        filtered_tasks = []
        
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')
        
        if not date_from and not date_to:
            return tasks
        
        for task in tasks:
            try:
                if task.get('created_at'):
                    task_date = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00')).date()
                    
                    if date_from and task_date < date.fromisoformat(date_from):
                        continue
                    if date_to and task_date > date.fromisoformat(date_to):
                        continue
                    
                    filtered_tasks.append(task)
            except (ValueError, TypeError):
                # Skip tasks with invalid dates
                continue
        
        return filtered_tasks
    
    def _generate_search_suggestions(self, query: str, search_terms: List[str], result_count: int) -> List[str]:
        """Generate helpful search suggestions"""
        suggestions = []
        
        # If no results, suggest broader search
        if result_count == 0:
            suggestions.extend([
                f"Try searching for individual words from: {query}",
                "Check spelling and try synonyms",
                "Use broader search terms",
                "Try searching in documents as well"
            ])
        
        # If few results, suggest refinements
        elif result_count < 3:
            suggestions.extend([
                "Try adding more specific terms",
                "Search by owner or priority",
                "Include date filters"
            ])
        
        # Common helpful suggestions
        if len(search_terms) == 1:
            suggestions.append(f"Try combining with other terms: {search_terms[0]} + [status/owner/priority]")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _generate_document_snippet(self, document: Dict[str, Any], search_terms: List[str]) -> str:
        """Generate a snippet showing search term context"""
        text = document.get('text', '')
        summary = document.get('summary', '')
        
        # Try to find snippet from summary first
        if summary and any(term in summary.lower() for term in search_terms):
            return summary[:200] + "..." if len(summary) > 200 else summary
        
        # Find snippet from text content
        for term in search_terms:
            term_index = text.lower().find(term)
            if term_index != -1:
                start = max(0, term_index - 50)
                end = min(len(text), term_index + 100)
                snippet = text[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                return snippet
        
        # Fallback to beginning of text
        return text[:150] + "..." if len(text) > 150 else text
    
    def _find_cross_references(self, tasks: List[Dict[str, Any]], documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find relationships between tasks and documents"""
        relations = []
        
        for task in tasks[:5]:  # Limit to top 5 tasks for performance
            task_id = task.get('id')
            if task_id:
                # Check if any documents are linked to this task
                linked_docs = self.task_repository.get_linked_documents(int(task_id))
                if linked_docs:
                    relations.append({
                        'type': 'task_documents',
                        'task_id': task_id,
                        'task_title': task.get('title'),
                        'document_count': len(linked_docs)
                    })
        
        return relations[:10]  # Limit relations
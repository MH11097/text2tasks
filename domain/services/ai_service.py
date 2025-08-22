"""AI service for smart automation features"""

from typing import List, Dict, Any, Optional
import logging
import re
from datetime import datetime

from ..entities.task import TaskEntity
from ..entities.document import DocumentEntity
from infrastructure.external.openai_client import LLMClient

logger = logging.getLogger(__name__)

class AIService:
    """AI service for smart automation and tagging"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
        # Predefined tag categories for better organization
        self.tag_categories = {
            'priority': ['urgent', 'high', 'medium', 'low'],
            'type': ['bug', 'feature', 'improvement', 'research', 'documentation', 'testing'],
            'domain': ['backend', 'frontend', 'database', 'api', 'ui', 'infrastructure'],
            'complexity': ['simple', 'moderate', 'complex', 'epic'],
            'phase': ['planning', 'development', 'testing', 'deployment', 'maintenance']
        }
    
    async def generate_smart_tags(self, task: TaskEntity) -> List[str]:
        """Generate intelligent tags for a task based on content analysis"""
        try:
            # Combine task title and description for analysis
            content = f"Title: {task.title}"
            if task.description:
                content += f"\nDescription: {task.description}"
            
            # Use rule-based tagging first (fast)
            rule_based_tags = self._extract_rule_based_tags(content)
            
            # Use AI for semantic tagging (slower but more intelligent)
            ai_tags = await self._extract_ai_tags(content)
            
            # Combine and deduplicate
            all_tags = list(set(rule_based_tags + ai_tags))
            
            # Filter and validate tags
            validated_tags = self._validate_tags(all_tags)
            
            logger.info(f"Generated {len(validated_tags)} smart tags for task: {task.title[:50]}")
            return validated_tags
            
        except Exception as e:
            logger.error(f"Error generating smart tags: {e}")
            return []
    
    def _extract_rule_based_tags(self, content: str) -> List[str]:
        """Extract tags using rule-based patterns"""
        tags = []
        content_lower = content.lower()
        
        # Priority indicators
        if any(word in content_lower for word in ['urgent', 'asap', 'critical', 'hotfix']):
            tags.append('urgent')
        elif any(word in content_lower for word in ['high priority', 'important', 'blocker']):
            tags.append('high')
        
        # Type indicators
        if any(word in content_lower for word in ['bug', 'error', 'fix', 'issue']):
            tags.append('bug')
        elif any(word in content_lower for word in ['feature', 'add', 'implement', 'create']):
            tags.append('feature')
        elif any(word in content_lower for word in ['improve', 'enhance', 'optimize', 'refactor']):
            tags.append('improvement')
        elif any(word in content_lower for word in ['research', 'investigate', 'analyze', 'study']):
            tags.append('research')
        elif any(word in content_lower for word in ['document', 'docs', 'readme', 'guide']):
            tags.append('documentation')
        elif any(word in content_lower for word in ['test', 'testing', 'qa', 'validation']):
            tags.append('testing')
        
        # Domain indicators
        if any(word in content_lower for word in ['api', 'endpoint', 'backend', 'server']):
            tags.append('backend')
        elif any(word in content_lower for word in ['ui', 'frontend', 'interface', 'component']):
            tags.append('frontend')
        elif any(word in content_lower for word in ['database', 'sql', 'query', 'migration']):
            tags.append('database')
        elif any(word in content_lower for word in ['deploy', 'infrastructure', 'docker', 'ci/cd']):
            tags.append('infrastructure')
        
        # Complexity indicators
        if any(word in content_lower for word in ['quick', 'simple', 'easy', 'minor']):
            tags.append('simple')
        elif any(word in content_lower for word in ['complex', 'major', 'architecture', 'system']):
            tags.append('complex')
        
        return tags
    
    async def _extract_ai_tags(self, content: str) -> List[str]:
        """Extract tags using AI semantic analysis"""
        try:
            prompt = f"""
            Analyze the following task content and suggest 3-5 relevant tags from these categories:
            
            Priority: urgent, high, medium, low
            Type: bug, feature, improvement, research, documentation, testing
            Domain: backend, frontend, database, api, ui, infrastructure
            Complexity: simple, moderate, complex, epic
            Phase: planning, development, testing, deployment, maintenance
            
            Task Content: {content}
            
            Return only the tags as a comma-separated list, no explanations:
            """
            
            # Use available LLM client method for chat completion
            response = await self.llm_client.answer_question(
                question=prompt,
                context=""
            )
            
            if response and 'answer' in response:
                tags_text = response['answer'].strip()
                # Parse comma-separated tags
                tags = [tag.strip().lower() for tag in tags_text.split(',') if tag.strip()]
                return tags[:5]  # Limit to 5 tags
            
        except Exception as e:
            logger.warning(f"AI tag extraction failed: {e}")
        
        return []
    
    def _validate_tags(self, tags: List[str]) -> List[str]:
        """Validate and filter tags against predefined categories"""
        valid_tags = []
        all_valid_tags = set()
        
        # Collect all valid tags from categories
        for category_tags in self.tag_categories.values():
            all_valid_tags.update(category_tags)
        
        for tag in tags:
            if tag.lower() in all_valid_tags:
                valid_tags.append(tag.lower())
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(valid_tags))
    
    def suggest_related_tasks(self, task: TaskEntity, existing_tasks: List[TaskEntity]) -> List[Dict[str, Any]]:
        """Suggest tasks related to the given task"""
        try:
            suggestions = []
            task_content = f"{task.title} {task.description or ''}".lower()
            
            for existing_task in existing_tasks:
                if existing_task.id == task.id:
                    continue
                
                existing_content = f"{existing_task.title} {existing_task.description or ''}".lower()
                
                # Simple similarity scoring
                similarity_score = self._calculate_similarity(task_content, existing_content)
                
                if similarity_score > 0.3:  # Threshold for relatedness
                    suggestions.append({
                        'task_id': existing_task.id,
                        'title': existing_task.title,
                        'similarity_score': similarity_score,
                        'status': existing_task.status,
                        'priority': getattr(existing_task, 'priority', 'medium')
                    })
            
            # Sort by similarity score and return top 5
            suggestions.sort(key=lambda x: x['similarity_score'], reverse=True)
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Error suggesting related tasks: {e}")
            return []
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate basic text similarity using word overlap"""
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def analyze_task_dependencies(self, tasks: List[TaskEntity]) -> Dict[str, Any]:
        """Analyze potential task dependencies and suggest relationships"""
        try:
            dependencies = []
            
            for i, task1 in enumerate(tasks):
                for j, task2 in enumerate(tasks[i+1:], i+1):
                    # Check if task1 might depend on task2 or vice versa
                    dependency_score = self._calculate_dependency_score(task1, task2)
                    
                    if dependency_score > 0.5:
                        dependencies.append({
                            'from_task_id': task1.id,
                            'to_task_id': task2.id,
                            'dependency_type': 'blocks',
                            'confidence': dependency_score,
                            'reason': self._explain_dependency(task1, task2)
                        })
            
            # Analyze critical path
            critical_path = self._identify_critical_path(tasks, dependencies)
            
            return {
                'dependencies': dependencies,
                'critical_path': critical_path,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing task dependencies: {e}")
            return {'dependencies': [], 'critical_path': []}
    
    def _calculate_dependency_score(self, task1: TaskEntity, task2: TaskEntity) -> float:
        """Calculate likelihood that task1 depends on task2"""
        # Simple heuristic: check for blocking keywords and content similarity
        task1_content = f"{task1.title} {task1.description or ''}".lower()
        task2_content = f"{task2.title} {task2.description or ''}".lower()
        
        dependency_keywords = [
            'after', 'before', 'requires', 'depends on', 'needs', 'prerequisite',
            'blocks', 'blocked by', 'waiting for', 'once', 'when'
        ]
        
        score = 0.0
        
        # Check for explicit dependency keywords
        for keyword in dependency_keywords:
            if keyword in task1_content and any(word in task2_content for word in task2.title.lower().split()):
                score += 0.4
        
        # Check content similarity
        similarity = self._calculate_similarity(task1_content, task2_content)
        score += similarity * 0.3
        
        # Check status-based dependencies (e.g., testing depends on development)
        if task1.status == 'blocked' and task2.status in ['new', 'in_progress']:
            score += 0.3
        
        return min(score, 1.0)
    
    def _explain_dependency(self, task1: TaskEntity, task2: TaskEntity) -> str:
        """Generate explanation for why tasks might be dependent"""
        return f"Task '{task1.title[:30]}...' appears to depend on '{task2.title[:30]}...' based on content analysis"
    
    def _identify_critical_path(self, tasks: List[TaskEntity], dependencies: List[Dict]) -> List[str]:
        """Identify critical path through task dependencies"""
        # Simple critical path identification
        task_ids = [str(task.id) for task in tasks]
        
        # Count incoming dependencies for each task
        dependency_counts = {task_id: 0 for task_id in task_ids}
        for dep in dependencies:
            dependency_counts[str(dep['to_task_id'])] += 1
        
        # Critical path starts with tasks that have most dependencies
        critical_tasks = sorted(task_ids, key=lambda x: dependency_counts[x], reverse=True)
        
        return critical_tasks[:5]  # Return top 5 critical tasks
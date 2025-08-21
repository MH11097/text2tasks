import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Tag,
  Lightbulb,
  X,
  Plus,
  Check,
  Clock,
  AlertTriangle,
  Zap,
  Brain,
  Target,
  TrendingUp,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface Task {
  id: number;
  title: string;
  status: 'new' | 'in_progress' | 'blocked' | 'done';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  description?: string;
  tags?: string[];
  created_at: string;
}

interface SmartAutomationProps {
  tasks: Task[];
  onApplyAutoTags?: (taskId: number, tags: string[]) => void;
  onCreateSuggestedTask?: (task: Partial<Task>) => void;
  className?: string;
}

interface AutoTagSuggestion {
  taskId: number;
  taskTitle: string;
  suggestedTags: string[];
  confidence: number;
  reasoning: string;
}

interface TaskSuggestion {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  estimatedEffort: string;
  reasoning: string;
  basedOn: string[];
}

export const SmartAutomation: React.FC<SmartAutomationProps> = ({
  tasks,
  onApplyAutoTags,
  onCreateSuggestedTask,
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState<'tags' | 'suggestions'>('tags');
  const [appliedSuggestions, setAppliedSuggestions] = useState<Set<string>>(new Set());
  const [dismissedSuggestions, setDismissedSuggestions] = useState<Set<string>>(new Set());

  // Generate auto-tag suggestions based on task content
  const autoTagSuggestions = useMemo((): AutoTagSuggestion[] => {
    const suggestions: AutoTagSuggestion[] = [];
    
    tasks.forEach(task => {
      const existingTags = new Set(task.tags?.map(tag => tag.toLowerCase()) || []);
      const suggestedTags: string[] = [];
      let confidence = 0;
      const reasons: string[] = [];

      const title = task.title.toLowerCase();
      const description = task.description?.toLowerCase() || '';
      const content = `${title} ${description}`;

      // Technical tags
      if (content.includes('api') || content.includes('endpoint') || content.includes('rest')) {
        suggestedTags.push('api');
        reasons.push('Contains API-related keywords');
        confidence += 20;
      }
      
      if (content.includes('frontend') || content.includes('ui') || content.includes('interface')) {
        suggestedTags.push('frontend');
        reasons.push('Frontend-related task');
        confidence += 20;
      }
      
      if (content.includes('backend') || content.includes('server') || content.includes('database')) {
        suggestedTags.push('backend');
        reasons.push('Backend-related task');
        confidence += 20;
      }
      
      if (content.includes('bug') || content.includes('fix') || content.includes('error')) {
        suggestedTags.push('bugfix');
        reasons.push('Bug fixing task');
        confidence += 25;
      }
      
      if (content.includes('test') || content.includes('testing') || content.includes('unit')) {
        suggestedTags.push('testing');
        reasons.push('Testing-related task');
        confidence += 20;
      }
      
      if (content.includes('doc') || content.includes('documentation') || content.includes('readme')) {
        suggestedTags.push('documentation');
        reasons.push('Documentation task');
        confidence += 20;
      }
      
      if (content.includes('refactor') || content.includes('cleanup') || content.includes('improve')) {
        suggestedTags.push('refactoring');
        reasons.push('Code improvement task');
        confidence += 15;
      }

      // Priority-based tags
      if (task.priority === 'urgent' || task.priority === 'high') {
        suggestedTags.push('critical');
        reasons.push('High priority task');
        confidence += 10;
      }

      // Status-based insights
      if (task.status === 'blocked') {
        suggestedTags.push('needs-review');
        reasons.push('Blocked status suggests review needed');
        confidence += 15;
      }

      // Filter out existing tags
      const newTags = suggestedTags.filter(tag => !existingTags.has(tag));
      
      if (newTags.length > 0 && confidence > 30) {
        suggestions.push({
          taskId: task.id,
          taskTitle: task.title,
          suggestedTags: newTags,
          confidence,
          reasoning: reasons.join(', '),
        });
      }
    });

    return suggestions.sort((a, b) => b.confidence - a.confidence);
  }, [tasks]);

  // Generate task suggestions based on patterns
  const taskSuggestions = useMemo((): TaskSuggestion[] => {
    const suggestions: TaskSuggestion[] = [];
    
    // Analyze task patterns
    const completedTasks = tasks.filter(t => t.status === 'done');
    const inProgressTasks = tasks.filter(t => t.status === 'in_progress');
    const allTags = Array.from(new Set(tasks.flatMap(t => t.tags || [])));

    // Suggest testing tasks for completed features
    completedTasks.forEach(task => {
      if (task.title.toLowerCase().includes('implement') && 
          !tasks.some(t => t.title.toLowerCase().includes('test') && 
                         t.title.toLowerCase().includes(task.title.split(' ')[1]))) {
        suggestions.push({
          id: `test-${task.id}`,
          title: `Add tests for ${task.title.replace('Implement ', '').toLowerCase()}`,
          description: `Create comprehensive tests for the newly implemented ${task.title.toLowerCase()} feature`,
          priority: 'medium',
          estimatedEffort: '2-4 hours',
          reasoning: 'New features should have accompanying tests',
          basedOn: [task.title],
        });
      }
    });

    // Suggest documentation for undocumented features
    if (!tasks.some(t => t.title.toLowerCase().includes('documentation'))) {
      suggestions.push({
        id: 'doc-update',
        title: 'Update project documentation',
        description: 'Review and update documentation to reflect recent changes and new features',
        priority: 'low',
        estimatedEffort: '3-5 hours',
        reasoning: 'No recent documentation tasks found',
        basedOn: ['Recent feature implementations'],
      });
    }

    // Suggest code review tasks
    if (inProgressTasks.length > 3) {
      suggestions.push({
        id: 'code-review',
        title: 'Schedule code review session',
        description: 'Review multiple in-progress features for code quality and consistency',
        priority: 'medium',
        estimatedEffort: '1-2 hours',
        reasoning: `${inProgressTasks.length} tasks in progress may benefit from review`,
        basedOn: inProgressTasks.map(t => t.title),
      });
    }

    // Suggest performance optimization
    if (tasks.some(t => t.title.toLowerCase().includes('performance') || 
                      t.title.toLowerCase().includes('optimize'))) {
      suggestions.push({
        id: 'perf-audit',
        title: 'Conduct performance audit',
        description: 'Analyze application performance and identify optimization opportunities',
        priority: 'medium',
        estimatedEffort: '4-6 hours',
        reasoning: 'Performance-related tasks suggest need for systematic audit',
        basedOn: ['Performance-related tasks'],
      });
    }

    // Filter out dismissed suggestions
    return suggestions.filter(s => !dismissedSuggestions.has(s.id));
  }, [tasks, dismissedSuggestions]);

  const handleApplyTags = (suggestion: AutoTagSuggestion) => {
    onApplyAutoTags?.(suggestion.taskId, suggestion.suggestedTags);
    setAppliedSuggestions(prev => new Set([...prev, `tags-${suggestion.taskId}`]));
  };

  const handleCreateSuggestedTask = (suggestion: TaskSuggestion) => {
    onCreateSuggestedTask?.({
      title: suggestion.title,
      description: suggestion.description,
      priority: suggestion.priority,
      status: 'new' as const,
    });
    setAppliedSuggestions(prev => new Set([...prev, suggestion.id]));
  };

  const handleDismissSuggestion = (id: string) => {
    setDismissedSuggestions(prev => new Set([...prev, id]));
  };

  return (
    <div className={className}>
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Smart Automation</h3>
            <p className="text-sm text-muted-foreground">
              AI-powered suggestions to improve your workflow
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-border">
          <button
            onClick={() => setActiveTab('tags')}
            className={cn(
              'pb-3 px-1 border-b-2 transition-colors text-sm font-medium',
              activeTab === 'tags'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <div className="flex items-center gap-2">
              <Tag className="h-4 w-4" />
              Auto-Tagging ({autoTagSuggestions.length})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('suggestions')}
            className={cn(
              'pb-3 px-1 border-b-2 transition-colors text-sm font-medium',
              activeTab === 'suggestions'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <div className="flex items-center gap-2">
              <Lightbulb className="h-4 w-4" />
              Task Suggestions ({taskSuggestions.length})
            </div>
          </button>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'tags' && (
            <motion.div
              key="tags"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {autoTagSuggestions.length === 0 ? (
                <div className="text-center py-8">
                  <Brain className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground">No auto-tagging suggestions available</p>
                  <p className="text-sm text-muted-foreground/75">
                    Create more tasks with detailed descriptions to get AI-powered tag suggestions
                  </p>
                </div>
              ) : (
                autoTagSuggestions.map((suggestion) => {
                  const isApplied = appliedSuggestions.has(`tags-${suggestion.taskId}`);
                  
                  return (
                    <motion.div
                      key={suggestion.taskId}
                      layout
                      className="border border-border rounded-lg p-4 hover:border-primary/50 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h4 className="font-medium text-foreground mb-1">
                            {suggestion.taskTitle}
                          </h4>
                          <p className="text-sm text-muted-foreground mb-2">
                            {suggestion.reasoning}
                          </p>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">
                              Confidence: {suggestion.confidence}%
                            </span>
                            <div className="w-16 h-1 bg-muted rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-primary rounded-full transition-all"
                                style={{ width: `${suggestion.confidence}%` }}
                              />
                            </div>
                          </div>
                        </div>
                        <div className="ml-4">
                          {isApplied ? (
                            <div className="flex items-center gap-2 text-green-500">
                              <Check className="h-4 w-4" />
                              <span className="text-sm font-medium">Applied</span>
                            </div>
                          ) : (
                            <button
                              onClick={() => handleApplyTags(suggestion)}
                              className="px-3 py-2 bg-primary text-primary-foreground text-sm rounded-md hover:bg-primary/90 transition-colors"
                            >
                              Apply Tags
                            </button>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {suggestion.suggestedTags.map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded-full text-xs"
                          >
                            <Tag className="h-3 w-3" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    </motion.div>
                  );
                })
              )}
            </motion.div>
          )}

          {activeTab === 'suggestions' && (
            <motion.div
              key="suggestions"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {taskSuggestions.length === 0 ? (
                <div className="text-center py-8">
                  <Target className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground">No task suggestions available</p>
                  <p className="text-sm text-muted-foreground/75">
                    Complete more tasks to unlock intelligent suggestions
                  </p>
                </div>
              ) : (
                taskSuggestions.map((suggestion) => {
                  const isApplied = appliedSuggestions.has(suggestion.id);
                  
                  return (
                    <motion.div
                      key={suggestion.id}
                      layout
                      className="border border-border rounded-lg p-4 hover:border-primary/50 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="font-medium text-foreground">{suggestion.title}</h4>
                            <span className={cn(
                              'px-2 py-1 rounded-full text-xs font-medium',
                              suggestion.priority === 'urgent' && 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200',
                              suggestion.priority === 'high' && 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200',
                              suggestion.priority === 'medium' && 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200',
                              suggestion.priority === 'low' && 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200'
                            )}>
                              {suggestion.priority}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">
                            {suggestion.description}
                          </p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {suggestion.estimatedEffort}
                            </span>
                            <span className="flex items-center gap-1">
                              <Brain className="h-3 w-3" />
                              {suggestion.reasoning}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4 flex items-center gap-2">
                          {isApplied ? (
                            <div className="flex items-center gap-2 text-green-500">
                              <Check className="h-4 w-4" />
                              <span className="text-sm font-medium">Created</span>
                            </div>
                          ) : (
                            <>
                              <button
                                onClick={() => handleDismissSuggestion(suggestion.id)}
                                className="p-2 text-muted-foreground hover:text-foreground rounded-md hover:bg-muted transition-colors"
                                title="Dismiss suggestion"
                              >
                                <X className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleCreateSuggestedTask(suggestion)}
                                className="px-3 py-2 bg-primary text-primary-foreground text-sm rounded-md hover:bg-primary/90 transition-colors flex items-center gap-1"
                              >
                                <Plus className="h-4 w-4" />
                                Create Task
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                      {suggestion.basedOn.length > 0 && (
                        <div className="pt-2 border-t border-border">
                          <p className="text-xs text-muted-foreground mb-1">Based on:</p>
                          <div className="flex flex-wrap gap-1">
                            {suggestion.basedOn.slice(0, 3).map((item, index) => (
                              <span
                                key={index}
                                className="px-2 py-1 bg-muted text-muted-foreground rounded text-xs"
                              >
                                {item}
                              </span>
                            ))}
                            {suggestion.basedOn.length > 3 && (
                              <span className="text-xs text-muted-foreground">
                                +{suggestion.basedOn.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  );
                })
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap,
  FileText,
  Play,
  Copy,
  Check,
  Clock,
  Target,
  Code,
  Bug,
  TestTube,
  Rocket,
  Star,
  Download,
  Search,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface Task {
  id: number;
  title: string;
  status: 'new' | 'in_progress' | 'blocked' | 'done';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  description?: string;
}

interface TaskTemplate {
  id: string;
  name: string;
  description: string;
  category: 'development' | 'testing' | 'documentation' | 'planning' | 'maintenance';
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  tasks: Array<{
    title: string;
    description: string;
    priority: 'low' | 'medium' | 'high' | 'urgent';
    estimatedHours?: number;
  }>;
  tags: string[];
  usageCount: number;
  isFavorite?: boolean;
}

interface QuickAction {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  action: () => void;
  shortcut?: string;
  category: 'creation' | 'organization' | 'automation' | 'analysis';
}

interface ProductivityFeaturesProps {
  tasks: Task[];
  onCreateFromTemplate?: (template: TaskTemplate) => void;
  onExecuteQuickAction?: (action: QuickAction) => void;
  onSaveAsTemplate?: (tasks: Task[]) => void;
  className?: string;
}

export const ProductivityFeatures: React.FC<ProductivityFeaturesProps> = ({
  tasks,
  onCreateFromTemplate,
  onExecuteQuickAction,
  onSaveAsTemplate,
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState<'templates' | 'actions'>('templates');
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [showCreateTemplate, setShowCreateTemplate] = useState(false);
  const [appliedActions, setAppliedActions] = useState<Set<string>>(new Set());

  // Built-in task templates
  const taskTemplates: TaskTemplate[] = [
    {
      id: 'feature-development',
      name: 'Feature Development',
      description: 'Complete workflow for implementing a new feature',
      category: 'development',
      icon: Code,
      color: 'bg-blue-500',
      usageCount: 12,
      isFavorite: true,
      tags: ['frontend', 'backend', 'fullstack'],
      tasks: [
        {
          title: 'Requirements gathering and analysis',
          description: 'Define feature requirements, user stories, and acceptance criteria',
          priority: 'high',
          estimatedHours: 4,
        },
        {
          title: 'Technical design and architecture',
          description: 'Create technical specification and architecture design',
          priority: 'high',
          estimatedHours: 6,
        },
        {
          title: 'Backend API implementation',
          description: 'Develop backend endpoints and business logic',
          priority: 'high',
          estimatedHours: 12,
        },
        {
          title: 'Frontend UI implementation',
          description: 'Build user interface components and integration',
          priority: 'medium',
          estimatedHours: 10,
        },
        {
          title: 'Unit and integration testing',
          description: 'Write comprehensive tests for the new feature',
          priority: 'medium',
          estimatedHours: 8,
        },
        {
          title: 'Code review and optimization',
          description: 'Peer review, optimization, and final adjustments',
          priority: 'medium',
          estimatedHours: 4,
        },
        {
          title: 'Documentation and deployment',
          description: 'Update docs and deploy to production',
          priority: 'low',
          estimatedHours: 3,
        },
      ],
    },
    {
      id: 'bug-fix-workflow',
      name: 'Bug Fix Workflow',
      description: 'Systematic approach to bug investigation and resolution',
      category: 'maintenance',
      icon: Bug,
      color: 'bg-red-500',
      usageCount: 8,
      tags: ['bugfix', 'debugging', 'maintenance'],
      tasks: [
        {
          title: 'Bug reproduction and analysis',
          description: 'Reproduce the bug and analyze root cause',
          priority: 'urgent',
          estimatedHours: 2,
        },
        {
          title: 'Impact assessment',
          description: 'Evaluate bug impact on users and system stability',
          priority: 'high',
          estimatedHours: 1,
        },
        {
          title: 'Fix implementation',
          description: 'Implement the bug fix with proper error handling',
          priority: 'high',
          estimatedHours: 4,
        },
        {
          title: 'Testing and validation',
          description: 'Test the fix and ensure no regression',
          priority: 'high',
          estimatedHours: 3,
        },
        {
          title: 'Code review and deployment',
          description: 'Review changes and deploy to production',
          priority: 'medium',
          estimatedHours: 2,
        },
      ],
    },
    {
      id: 'testing-suite',
      name: 'Testing Suite Setup',
      description: 'Comprehensive testing setup for a project or feature',
      category: 'testing',
      icon: TestTube,
      color: 'bg-green-500',
      usageCount: 6,
      tags: ['testing', 'quality', 'automation'],
      tasks: [
        {
          title: 'Test strategy planning',
          description: 'Define testing approach and coverage requirements',
          priority: 'high',
          estimatedHours: 3,
        },
        {
          title: 'Unit tests implementation',
          description: 'Write unit tests for all components and functions',
          priority: 'high',
          estimatedHours: 8,
        },
        {
          title: 'Integration tests setup',
          description: 'Create integration tests for API endpoints',
          priority: 'medium',
          estimatedHours: 6,
        },
        {
          title: 'E2E test automation',
          description: 'Implement end-to-end testing scenarios',
          priority: 'medium',
          estimatedHours: 10,
        },
        {
          title: 'Performance testing',
          description: 'Set up performance benchmarks and load testing',
          priority: 'low',
          estimatedHours: 5,
        },
      ],
    },
    {
      id: 'documentation-update',
      name: 'Documentation Update',
      description: 'Complete documentation refresh for a project',
      category: 'documentation',
      icon: FileText,
      color: 'bg-purple-500',
      usageCount: 4,
      tags: ['documentation', 'maintenance', 'knowledge'],
      tasks: [
        {
          title: 'Audit existing documentation',
          description: 'Review current docs for accuracy and completeness',
          priority: 'medium',
          estimatedHours: 4,
        },
        {
          title: 'Update API documentation',
          description: 'Refresh API docs with latest endpoints and examples',
          priority: 'medium',
          estimatedHours: 6,
        },
        {
          title: 'User guide updates',
          description: 'Update user guides and tutorials',
          priority: 'medium',
          estimatedHours: 8,
        },
        {
          title: 'Developer onboarding docs',
          description: 'Update setup and development workflow docs',
          priority: 'low',
          estimatedHours: 4,
        },
      ],
    },
    {
      id: 'project-planning',
      name: 'Project Planning',
      description: 'Complete project planning and setup workflow',
      category: 'planning',
      icon: Target,
      color: 'bg-orange-500',
      usageCount: 3,
      tags: ['planning', 'organization', 'strategy'],
      tasks: [
        {
          title: 'Project scope definition',
          description: 'Define project goals, scope, and constraints',
          priority: 'high',
          estimatedHours: 6,
        },
        {
          title: 'Resource planning',
          description: 'Plan team resources and timeline',
          priority: 'high',
          estimatedHours: 4,
        },
        {
          title: 'Risk assessment',
          description: 'Identify and plan mitigation for project risks',
          priority: 'medium',
          estimatedHours: 3,
        },
        {
          title: 'Milestone planning',
          description: 'Define project milestones and deliverables',
          priority: 'medium',
          estimatedHours: 3,
        },
        {
          title: 'Communication plan',
          description: 'Set up project communication and reporting',
          priority: 'low',
          estimatedHours: 2,
        },
      ],
    },
  ];

  // Quick actions
  const quickActions: QuickAction[] = [
    {
      id: 'bulk-status-update',
      name: 'Bulk Status Update',
      description: 'Update status for multiple selected tasks',
      icon: Check,
      color: 'bg-green-500',
      category: 'organization',
      shortcut: 'Ctrl+Shift+U',
      action: () => console.log('Bulk status update'),
    },
    {
      id: 'auto-priority-sort',
      name: 'Smart Priority Sort',
      description: 'Automatically sort tasks by AI-suggested priority',
      icon: Target,
      color: 'bg-blue-500',
      category: 'automation',
      shortcut: 'Ctrl+Shift+P',
      action: () => console.log('Auto priority sort'),
    },
    {
      id: 'duplicate-task',
      name: 'Duplicate Selected Tasks',
      description: 'Create copies of selected tasks with modifications',
      icon: Copy,
      color: 'bg-purple-500',
      category: 'creation',
      shortcut: 'Ctrl+D',
      action: () => console.log('Duplicate tasks'),
    },
    {
      id: 'time-blocking',
      name: 'Generate Time Blocks',
      description: 'Create calendar time blocks for upcoming tasks',
      icon: Clock,
      color: 'bg-orange-500',
      category: 'organization',
      shortcut: 'Ctrl+T',
      action: () => console.log('Generate time blocks'),
    },
    {
      id: 'dependency-analysis',
      name: 'Dependency Analysis',
      description: 'Analyze and visualize task dependencies',
      icon: Zap,
      color: 'bg-yellow-500',
      category: 'analysis',
      shortcut: 'Ctrl+Shift+D',
      action: () => console.log('Dependency analysis'),
    },
    {
      id: 'export-report',
      name: 'Export Progress Report',
      description: 'Generate and export detailed progress report',
      icon: Download,
      color: 'bg-indigo-500',
      category: 'analysis',
      shortcut: 'Ctrl+E',
      action: () => console.log('Export report'),
    },
  ];

  // Filter templates
  const filteredTemplates = taskTemplates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = categoryFilter === 'all' || template.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  // Filter actions
  const filteredActions = quickActions.filter(action => {
    const matchesSearch = action.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         action.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || action.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const handleUseTemplate = (template: TaskTemplate) => {
    onCreateFromTemplate?.(template);
  };

  const handleExecuteAction = (action: QuickAction) => {
    action.action();
    onExecuteQuickAction?.(action);
    setAppliedActions(prev => new Set([...prev, action.id]));
    
    // Remove from applied actions after 3 seconds
    setTimeout(() => {
      setAppliedActions(prev => {
        const newSet = new Set(prev);
        newSet.delete(action.id);
        return newSet;
      });
    }, 3000);
  };

  return (
    <div className={className}>
      <div className="bg-card border border-border rounded-lg p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
            <Rocket className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Productivity Features</h3>
            <p className="text-sm text-muted-foreground">
              Templates, quick actions, and workflow automation
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-border">
          <button
            onClick={() => setActiveTab('templates')}
            className={cn(
              'pb-3 px-1 border-b-2 transition-colors text-sm font-medium',
              activeTab === 'templates'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Task Templates ({taskTemplates.length})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('actions')}
            className={cn(
              'pb-3 px-1 border-b-2 transition-colors text-sm font-medium',
              activeTab === 'actions'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Quick Actions ({quickActions.length})
            </div>
          </button>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder={`Search ${activeTab}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All Categories</option>
            {activeTab === 'templates' ? (
              <>
                <option value="development">Development</option>
                <option value="testing">Testing</option>
                <option value="documentation">Documentation</option>
                <option value="planning">Planning</option>
                <option value="maintenance">Maintenance</option>
              </>
            ) : (
              <>
                <option value="creation">Creation</option>
                <option value="organization">Organization</option>
                <option value="automation">Automation</option>
                <option value="analysis">Analysis</option>
              </>
            )}
          </select>
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'templates' && (
            <motion.div
              key="templates"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {filteredTemplates.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground">No templates found</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {filteredTemplates.map((template) => {
                    const IconComponent = template.icon;
                    const totalHours = template.tasks.reduce((acc, task) => acc + (task.estimatedHours || 0), 0);
                    
                    return (
                      <motion.div
                        key={template.id}
                        layout
                        className="border border-border rounded-lg p-4 hover:border-primary/50 transition-all hover:shadow-lg"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', template.color)}>
                              <IconComponent className="h-5 w-5 text-white" />
                            </div>
                            <div>
                              <h4 className="font-medium text-foreground flex items-center gap-2">
                                {template.name}
                                {template.isFavorite && <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />}
                              </h4>
                              <p className="text-sm text-muted-foreground">{template.description}</p>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                          <span>{template.tasks.length} tasks</span>
                          <span>{totalHours}h estimated</span>
                          <span>{template.usageCount} uses</span>
                        </div>

                        <div className="flex flex-wrap gap-1 mb-3">
                          {template.tags.map((tag, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>

                        <div className="space-y-2 mb-4">
                          {template.tasks.slice(0, 3).map((task, index) => (
                            <div key={index} className="text-sm">
                              <div className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full" />
                                <span className="text-foreground">{task.title}</span>
                                <span className="text-muted-foreground">({task.estimatedHours}h)</span>
                              </div>
                            </div>
                          ))}
                          {template.tasks.length > 3 && (
                            <div className="text-sm text-muted-foreground">
                              +{template.tasks.length - 3} more tasks...
                            </div>
                          )}
                        </div>

                        <button
                          onClick={() => handleUseTemplate(template)}
                          className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
                        >
                          <Play className="h-4 w-4" />
                          Use Template
                        </button>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'actions' && (
            <motion.div
              key="actions"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {filteredActions.length === 0 ? (
                <div className="text-center py-8">
                  <Zap className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground">No quick actions found</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredActions.map((action) => {
                    const IconComponent = action.icon;
                    const isApplied = appliedActions.has(action.id);
                    
                    return (
                      <motion.div
                        key={action.id}
                        layout
                        className={cn(
                          'border rounded-lg p-4 transition-all cursor-pointer',
                          isApplied 
                            ? 'border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-950/30'
                            : 'border-border bg-background hover:border-primary/50 hover:shadow-md'
                        )}
                        onClick={() => !isApplied && handleExecuteAction(action)}
                      >
                        <div className="flex items-center gap-3 mb-2">
                          <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center', action.color)}>
                            {isApplied ? (
                              <Check className="h-4 w-4 text-white" />
                            ) : (
                              <IconComponent className="h-4 w-4 text-white" />
                            )}
                          </div>
                          <div className="flex-1">
                            <h4 className="font-medium text-foreground">{action.name}</h4>
                            {action.shortcut && (
                              <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                                {action.shortcut}
                              </span>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">{action.description}</p>
                        <div className="text-xs text-muted-foreground capitalize">
                          {action.category}
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
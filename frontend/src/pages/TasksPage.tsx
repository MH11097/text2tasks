import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Search,
  Filter,
  MoreVertical,
  Grid3X3,
  List,
  Calendar,
  CheckSquare,
  Clock,
  AlertCircle,
  CheckCircle,
  User,
  X,
  Edit3,
  Trash2,
  Play,
  Pause,
  BarChart3,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Network,
  Rocket,
  MoreHorizontal,
} from 'lucide-react';

import { api } from '@/services/api';
import { useUI } from '@/stores/app-store';
import { cn } from '@/utils/cn';
import { formatRelativeTime } from '@/utils/format';
import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard';
import { SmartAutomation } from '@/components/analytics/SmartAutomation';
import { TaskRelationships } from '@/components/analytics/TaskRelationships';
import { ProductivityFeatures } from '@/components/analytics/ProductivityFeatures';
import { VirtualizedTaskList, useVirtualizedListHeight } from '@/components/common/VirtualizedList';
import { Task } from '@/types/api';

interface TaskFilters {
  status?: string[];
  priority?: string[];
  owner?: string[];
  search?: string;
}

type ViewMode = 'list' | 'grid' | 'kanban';

const statusConfig = {
  new: { icon: Clock, color: 'text-gray-500', bgColor: 'bg-gray-100 dark:bg-gray-800', label: 'New' },
  in_progress: { icon: Play, color: 'text-blue-500', bgColor: 'bg-blue-100 dark:bg-blue-900', label: 'In Progress' },
  blocked: { icon: AlertCircle, color: 'text-red-500', bgColor: 'bg-red-100 dark:bg-red-900', label: 'Blocked' },
  done: { icon: CheckCircle, color: 'text-green-500', bgColor: 'bg-green-100 dark:bg-green-900', label: 'Done' },
};

const priorityConfig = {
  low: { color: 'text-gray-500', bgColor: 'bg-gray-100 dark:bg-gray-800', label: 'Low' },
  medium: { color: 'text-yellow-500', bgColor: 'bg-yellow-100 dark:bg-yellow-900', label: 'Medium' },
  high: { color: 'text-orange-500', bgColor: 'bg-orange-100 dark:bg-orange-900', label: 'High' },
  urgent: { color: 'text-red-500', bgColor: 'bg-red-100 dark:bg-red-900', label: 'Urgent' },
};

// Task Card Component
interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (id: number) => void;
  onStatusChange: (id: number, status: Task['status']) => void;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, onEdit, onDelete, onStatusChange }) => {
  const [showMenu, setShowMenu] = useState(false);
  const StatusIcon = statusConfig[task.status].icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="group bg-card border border-border rounded-lg p-4 hover:shadow-md transition-all duration-200"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={cn(
            'flex items-center justify-center w-8 h-8 rounded-lg',
            statusConfig[task.status].bgColor
          )}>
            <StatusIcon className={cn('h-4 w-4', statusConfig[task.status].color)} />
          </div>
          <div>
            <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2">
              {task.title}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className={cn(
                'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                statusConfig[task.status].bgColor,
                statusConfig[task.status].color
              )}>
                {statusConfig[task.status].label}
              </span>
              {task.priority && (
                <span className={cn(
                  'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                  priorityConfig[task.priority].bgColor,
                  priorityConfig[task.priority].color
                )}>
                  {priorityConfig[task.priority].label}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Menu */}
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(!showMenu);
            }}
            className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-muted transition-all"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
          
          {showMenu && (
            <div className="absolute right-0 top-8 w-48 bg-popover border border-border rounded-md shadow-lg z-10">
              <div className="py-1">
                <button
                  onClick={() => { onEdit(task); setShowMenu(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-muted text-left"
                >
                  <Edit3 className="h-4 w-4" />
                  Edit Task
                </button>
                <hr className="my-1" />
                {Object.entries(statusConfig).map(([status, config]) => (
                  <button
                    key={status}
                    onClick={() => {
                      onStatusChange(task.id, status as Task['status']);
                      setShowMenu(false);
                    }}
                    className={cn(
                      'flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-muted text-left',
                      task.status === status && 'bg-primary/10 text-primary'
                    )}
                  >
                    <config.icon className="h-4 w-4" />
                    Mark as {config.label}
                  </button>
                ))}
                <hr className="my-1" />
                <button
                  onClick={() => { onDelete(task.id); setShowMenu(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-destructive/10 text-destructive text-left"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Task
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Description */}
      {task.description && (
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
          {task.description}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <div className="flex items-center gap-3">
          {task.owner && (
            <div className="flex items-center gap-1">
              <User className="h-4 w-4" />
              <span>{task.owner}</span>
            </div>
          )}
          {task.due_date && (
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>{formatRelativeTime(task.due_date)}</span>
            </div>
          )}
        </div>
        <span className="text-xs">{formatRelativeTime(task.created_at)}</span>
      </div>
    </motion.div>
  );
};

// Main TasksPage Component
export const TasksPage: React.FC = () => {
  const { setCurrentView } = useUI();
  const queryClient = useQueryClient();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<TaskFilters>({});
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [showAutomation, setShowAutomation] = useState(false);
  const [showRelationships, setShowRelationships] = useState(false);
  const [showProductivity, setShowProductivity] = useState(false);
  const [showAdvancedMenu, setShowAdvancedMenu] = useState(false);

  React.useEffect(() => {
    setCurrentView('tasks');
  }, [setCurrentView]);

  // Fetch tasks
  const { data: tasks = [], isLoading, error } = useQuery({
    queryKey: ['tasks', selectedFilters],
    queryFn: () => api.tasks.getTasks(selectedFilters),
  });

  // Update task mutation
  const updateTaskMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Task> }) =>
      api.tasks.updateTask(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Delete task mutation
  const deleteTaskMutation = useMutation({
    mutationFn: (id: number) => api.tasks.deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Filter tasks based on search
  const filteredTasks = useMemo(() => {
    let filtered = tasks;

    if (searchQuery) {
      filtered = filtered.filter(task =>
        task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        task.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        task.owner?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    return filtered;
  }, [tasks, searchQuery]);

  const handleStatusChange = (id: number, status: Task['status']) => {
    updateTaskMutation.mutate({ id, data: { status } });
  };

  const handleEdit = (task: Task) => {
    setEditingTask(task);
    setShowCreateModal(true);
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this task?')) {
      deleteTaskMutation.mutate(id);
    }
  };

  const handleFilterChange = (key: keyof TaskFilters, value: string[]) => {
    setSelectedFilters(prev => ({
      ...prev,
      [key]: value.length > 0 ? value : undefined
    }));
  };

  // Get task counts by status
  const taskCounts = useMemo(() => {
    return tasks.reduce((acc, task) => {
      acc[task.status] = (acc[task.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [tasks]);

  // Virtual scrolling configuration
  const TASK_CARD_HEIGHT = 180; // Approximate height of a task card
  const MAX_CONTAINER_HEIGHT = 800; // Maximum height before scrolling
  const containerHeight = useVirtualizedListHeight(
    MAX_CONTAINER_HEIGHT,
    TASK_CARD_HEIGHT,
    filteredTasks.length,
    24 // gap between items
  );

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">Failed to load tasks</h3>
          <p className="text-muted-foreground">Please try refreshing the page</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border bg-card/50">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-foreground">Tasks</h1>
              <p className="text-muted-foreground">
                Manage your tasks and track progress
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowAnalytics(!showAnalytics)}
                  className="inline-flex items-center gap-2 px-3 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
                >
                  <BarChart3 className="h-4 w-4" />
                  Analytics
                  {showAnalytics ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
                <button
                  onClick={() => setShowAutomation(!showAutomation)}
                  className="inline-flex items-center gap-2 px-3 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
                >
                  <Sparkles className="h-4 w-4" />
                  AI Assistant
                  {showAutomation ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
                
                {/* Advanced Features Menu */}
                <div className="relative">
                  <button
                    onClick={() => setShowAdvancedMenu(!showAdvancedMenu)}
                    className="inline-flex items-center gap-2 px-3 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
                  >
                    <MoreHorizontal className="h-4 w-4" />
                    More
                  </button>
                  
                  {showAdvancedMenu && (
                    <div className="absolute right-0 top-12 w-64 bg-popover border border-border rounded-lg shadow-lg z-10">
                      <div className="p-2">
                        <button
                          onClick={() => {
                            setShowRelationships(!showRelationships);
                            setShowAdvancedMenu(false);
                          }}
                          className="flex items-center gap-3 w-full px-3 py-2 text-sm rounded-lg hover:bg-muted transition-colors"
                        >
                          <Network className="h-4 w-4" />
                          <div className="text-left">
                            <div className="font-medium">Task Relationships</div>
                            <div className="text-xs text-muted-foreground">Dependencies and connections</div>
                          </div>
                        </button>
                        <button
                          onClick={() => {
                            setShowProductivity(!showProductivity);
                            setShowAdvancedMenu(false);
                          }}
                          className="flex items-center gap-3 w-full px-3 py-2 text-sm rounded-lg hover:bg-muted transition-colors"
                        >
                          <Rocket className="h-4 w-4" />
                          <div className="text-left">
                            <div className="font-medium">Productivity Tools</div>
                            <div className="text-xs text-muted-foreground">Templates and quick actions</div>
                          </div>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Plus className="h-4 w-4" />
                New Task
              </button>
            </div>
          </div>

          {/* Search and Controls */}
          <div className="flex items-center gap-4 mb-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search tasks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center border border-border rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  'p-2 rounded-md transition-colors',
                  viewMode === 'grid' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                )}
              >
                <Grid3X3 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'p-2 rounded-md transition-colors',
                  viewMode === 'list' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                )}
              >
                <List className="h-4 w-4" />
              </button>
            </div>

            {/* Filters */}
            <button className="inline-flex items-center gap-2 px-3 py-2 border border-border rounded-lg hover:bg-muted transition-colors">
              <Filter className="h-4 w-4" />
              Filters
            </button>
          </div>

          {/* Status Summary */}
          <div className="flex items-center gap-6">
            {Object.entries(statusConfig).map(([status, config]) => (
              <div key={status} className="flex items-center gap-2">
                <config.icon className={cn('h-4 w-4', config.color)} />
                <span className="text-sm font-medium text-foreground">
                  {config.label}: {taskCounts[status] || 0}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Analytics Dashboard */}
      {showAnalytics && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="border-b border-border bg-muted/30"
        >
          <div className="p-6">
            <AnalyticsDashboard tasks={filteredTasks} />
          </div>
        </motion.div>
      )}

      {/* Smart Automation */}
      {showAutomation && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="border-b border-border bg-muted/30"
        >
          <div className="p-6">
            <SmartAutomation 
              tasks={filteredTasks} 
              onApplyAutoTags={(taskId, tags) => {
                // TODO: Implement auto-tag application
                console.log('Apply tags to task', taskId, tags);
              }}
              onCreateSuggestedTask={(task) => {
                // TODO: Implement suggested task creation
                console.log('Create suggested task', task);
              }}
            />
          </div>
        </motion.div>
      )}

      {/* Task Relationships */}
      {showRelationships && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="border-b border-border bg-muted/30"
        >
          <div className="p-6">
            <TaskRelationships 
              tasks={filteredTasks}
              onCreateDependency={(taskId, dependsOnId) => {
                // TODO: Implement dependency creation
                console.log('Create dependency', taskId, 'depends on', dependsOnId);
              }}
              onRemoveDependency={(taskId, dependsOnId) => {
                // TODO: Implement dependency removal
                console.log('Remove dependency', taskId, 'from', dependsOnId);
              }}
            />
          </div>
        </motion.div>
      )}

      {/* Productivity Features */}
      {showProductivity && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="border-b border-border bg-muted/30"
        >
          <div className="p-6">
            <ProductivityFeatures 
              tasks={filteredTasks}
              onCreateFromTemplate={(template) => {
                // TODO: Implement template-based task creation
                console.log('Create tasks from template', template);
              }}
              onExecuteQuickAction={(action) => {
                // TODO: Implement quick action execution
                console.log('Execute quick action', action);
              }}
              onSaveAsTemplate={(tasks) => {
                // TODO: Implement save as template
                console.log('Save tasks as template', tasks);
              }}
            />
          </div>
        </motion.div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading tasks...</p>
            </div>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <CheckSquare className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {searchQuery ? 'No tasks found' : 'No tasks yet'}
            </h3>
            <p className="text-muted-foreground mb-6 max-w-md">
              {searchQuery
                ? 'No tasks match your search criteria. Try adjusting your search terms.'
                : 'Get started by creating your first task to track your work.'}
            </p>
            <div className="space-y-4">
            <button
              onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
                Create First Task
                </button>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground mb-2">Or try our smart features:</p>
                  <div className="flex justify-center gap-2">
                    <button
                      onClick={() => setShowAnalytics(!showAnalytics)}
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs border border-border rounded-md hover:bg-muted transition-colors"
                    >
                      <BarChart3 className="h-3 w-3" />
                      View Analytics
                    </button>
                    <button
                      onClick={() => setShowAutomation(!showAutomation)}
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs border border-border rounded-md hover:bg-muted transition-colors"
                    >
                      <Sparkles className="h-3 w-3" />
                      AI Suggestions
                    </button>
                    <button
                      onClick={() => setShowRelationships(!showRelationships)}
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs border border-border rounded-md hover:bg-muted transition-colors"
                    >
                      <Network className="h-3 w-3" />
                      Task Relations
                    </button>
                    <button
                      onClick={() => setShowProductivity(!showProductivity)}
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs border border-border rounded-md hover:bg-muted transition-colors"
                    >
                      <Rocket className="h-3 w-3" />
                      Templates
                    </button>
                  </div>
                </div>
              </div>
          </div>
        ) : viewMode === 'grid' ? (
          <motion.div
            layout
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            <AnimatePresence>
              {filteredTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onStatusChange={handleStatusChange}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        ) : (
          // Use virtualized list for list view when there are many tasks
          <VirtualizedTaskList
            tasks={filteredTasks}
            itemHeight={TASK_CARD_HEIGHT}
            containerHeight={containerHeight}
            renderTask={(task, index) => (
              <TaskCard
                key={task.id}
                task={task}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onStatusChange={handleStatusChange}
              />
            )}
            className="w-full"
            enableAnimations={filteredTasks.length <= 50} // Disable animations for very large lists
          />
        )}
      </div>

      {/* Create/Edit Task Modal - TODO: Implement */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">
              {editingTask ? 'Edit Task' : 'Create New Task'}
            </h2>
            <p className="text-muted-foreground mb-4">
              Task creation form will be implemented here.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingTask(null);
                }}
                className="px-4 py-2 text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingTask(null);
                }}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
              >
                {editingTask ? 'Save Changes' : 'Create Task'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
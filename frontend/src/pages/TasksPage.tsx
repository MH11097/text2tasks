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
  FileText,
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
  onSelect: (task: Task) => void;
  onEdit: (task: Task) => void;
  onDelete: (id: number) => void;
  onStatusChange: (id: number, status: Task['status']) => void;
}

// Task Form Modal Component
interface TaskFormModalProps {
  task?: Task | null;
  onClose: () => void;
  onSave: (taskData: any) => Promise<void>;
}

const TaskFormModal: React.FC<TaskFormModalProps> = ({ task, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    title: task?.title || '',
    description: task?.description || '',
    priority: task?.priority || 'medium',
    due_date: task?.due_date || '',
    owner: task?.owner || '',
    created_by: 'user',
    document_ids: task?.linked_document_ids || []
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch available documents for linking
  const { data: availableDocuments = [] } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      try {
        const response = await api.documents.getDocuments();
        return response.documents || response;
      } catch (error) {
        console.log('Failed to fetch documents:', error);
        return [];
      }
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) return;
    
    setIsSubmitting(true);
    try {
      await onSave(formData);
    } catch (error) {
      console.error('Error saving task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-semibold mb-4">
          {task ? 'Edit Task' : 'Create New Task'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter task title..."
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter task description..."
              rows={3}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Due Date</label>
              <input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Owner</label>
            <input
              type="text"
              value={formData.owner}
              onChange={(e) => setFormData(prev => ({ ...prev, owner: e.target.value }))}
              className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter owner name..."
            />
          </div>
          
          {/* Document Linking */}
          <div>
            <label className="block text-sm font-medium mb-1">Link Documents (Optional)</label>
            <div className="space-y-2">
              {availableDocuments.length > 0 ? (
                <div className="max-h-32 overflow-y-auto border border-input rounded-lg p-2">
                  {availableDocuments.map((doc: any) => (
                    <label key={doc.id} className="flex items-center gap-2 p-1 hover:bg-muted/50 rounded text-sm">
                      <input
                        type="checkbox"
                        checked={formData.document_ids.includes(doc.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData(prev => ({ 
                              ...prev, 
                              document_ids: [...prev.document_ids, doc.id] 
                            }));
                          } else {
                            setFormData(prev => ({ 
                              ...prev, 
                              document_ids: prev.document_ids.filter(id => id !== doc.id) 
                            }));
                          }
                        }}
                        className="rounded"
                      />
                      <FileText className="h-3 w-3 text-blue-500" />
                      <span className="truncate">{doc.title || `Document #${doc.id}`}</span>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No documents available to link</p>
              )}
              {formData.document_ids.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {formData.document_ids.length} document(s) selected
                </p>
              )}
            </div>
          </div>
          
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-muted-foreground hover:text-foreground"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!formData.title.trim() || isSubmitting}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Saving...' : task ? 'Save Changes' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const TaskCard: React.FC<TaskCardProps> = ({ task, onSelect, onEdit, onDelete, onStatusChange }) => {
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
            <h3 
              className="font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2 cursor-pointer hover:underline"
              onClick={() => onSelect(task)}
            >
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

// Task Detail Panel Component
interface TaskDetailPanelProps {
  task: Task;
  onClose: () => void;
  onEdit: (task: Task) => void;
  onDelete: (id: number) => void;
  onStatusChange: (id: number, status: Task['status']) => void;
}

const TaskDetailPanel: React.FC<TaskDetailPanelProps> = ({ 
  task, 
  onClose, 
  onEdit, 
  onDelete, 
  onStatusChange 
}) => {
  const StatusIcon = statusConfig[task.status].icon;
  const priorityInfo = priorityConfig[task.priority];

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="fixed right-0 top-0 h-full w-96 bg-card border-l border-border shadow-xl z-40 overflow-y-auto"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={cn(
              'flex items-center justify-center w-10 h-10 rounded-lg',
              statusConfig[task.status].bgColor
            )}>
              <StatusIcon className={cn('h-5 w-5', statusConfig[task.status].color)} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">{task.title}</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className={cn(
                  'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                  priorityInfo.bgColor,
                  priorityInfo.color
                )}>
                  {priorityInfo.label}
                </span>
                <span className={cn(
                  'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                  statusConfig[task.status].bgColor,
                  statusConfig[task.status].color
                )}>
                  {statusConfig[task.status].label}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-6">
          {/* Description */}
          {task.description && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Description</h3>
              <p className="text-sm text-foreground whitespace-pre-wrap">{task.description}</p>
            </div>
          )}

          {/* Details */}
          <div className="grid grid-cols-2 gap-4">
            {task.owner && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Owner</h3>
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{task.owner}</span>
                </div>
              </div>
            )}

            {task.due_date && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Due Date</h3>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{task.due_date}</span>
                </div>
              </div>
            )}

            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Created</h3>
              <span className="text-sm">{formatRelativeTime(task.created_at)}</span>
            </div>

            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Updated</h3>
              <span className="text-sm">{formatRelativeTime(task.updated_at)}</span>
            </div>
          </div>

          {/* Status Actions */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Change Status</h3>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(statusConfig).map(([status, config]) => {
                const Icon = config.icon;
                const isCurrentStatus = status === task.status;
                
                return (
                  <button
                    key={status}
                    onClick={() => !isCurrentStatus && onStatusChange(task.id, status as Task['status'])}
                    disabled={isCurrentStatus}
                    className={cn(
                      'flex items-center gap-2 p-2 rounded-lg text-sm font-medium transition-colors',
                      isCurrentStatus
                        ? 'bg-primary text-primary-foreground cursor-default'
                        : 'bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {config.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Linked Documents */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Linked Documents</h3>
            {task.linked_document_ids && task.linked_document_ids.length > 0 ? (
              <div className="space-y-2">
                {task.linked_document_ids.map((docId) => (
                  <div key={docId} className="flex items-center gap-2 p-2 bg-muted/50 rounded-lg">
                    <FileText className="h-4 w-4 text-blue-500" />
                    <span className="text-sm">Document #{docId}</span>
                  </div>
                ))}
                <button className="text-xs text-primary hover:text-primary/80 transition-colors">
                  + Link More Documents
                </button>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">
                <p>No documents linked to this task</p>
                <button className="text-primary hover:text-primary/80 transition-colors mt-1">
                  + Link Documents
                </button>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="pt-4 border-t border-border">
            <div className="flex gap-2">
              <button
                onClick={() => onEdit(task)}
                className="flex items-center gap-2 px-3 py-2 bg-muted hover:bg-muted/80 rounded-lg text-sm font-medium transition-colors"
              >
                <Edit3 className="h-4 w-4" />
                Edit
              </button>
              <button
                onClick={() => onDelete(task.id)}
                className="flex items-center gap-2 px-3 py-2 bg-destructive/10 hover:bg-destructive/20 text-destructive rounded-lg text-sm font-medium transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
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
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  React.useEffect(() => {
    setCurrentView('tasks');
  }, [setCurrentView]);

  // Fetch tasks
  const { data: tasks = [], isLoading, error } = useQuery({
    queryKey: ['tasks', selectedFilters],
    queryFn: async () => {
      try {
        return await api.tasks.getTasks(selectedFilters);
      } catch (error) {
        console.error('Failed to fetch tasks:', error);
        // Fallback to mock data for development
        return [
          {
            id: 1,
            title: 'Implement task management system',
            description: 'Build a comprehensive task management system with create, read, update, and delete functionality.',
            status: 'in_progress',
            priority: 'high',
            owner: 'john.doe',
            due_date: '2024-12-25',
            created_at: '2024-12-20T10:00:00Z',
            updated_at: '2024-12-21T15:30:00Z',
            source_doc_id: '1',
            linked_document_ids: [1, 2],
          },
          {
            id: 2,
            title: 'Design user interface mockups',
            description: 'Create detailed UI mockups for the new dashboard interface.',
            status: 'done',
            priority: 'medium',
            owner: 'jane.smith',
            due_date: '2024-12-22',
            created_at: '2024-12-18T09:00:00Z',
            updated_at: '2024-12-20T14:00:00Z',
            source_doc_id: '2',
            linked_document_ids: [],
          },
          {
            id: 3,
            title: 'Write API documentation',
            description: 'Document all API endpoints with examples and response schemas.',
            status: 'new',
            priority: 'low',
            owner: 'mike.wilson',
            due_date: '2024-12-30',
            created_at: '2024-12-21T11:00:00Z',
            updated_at: '2024-12-21T11:00:00Z',
            source_doc_id: null,
            linked_document_ids: [1],
          },
          {
            id: 4,
            title: 'Fix database connection issues',
            description: 'Resolve intermittent database connection problems in production.',
            status: 'blocked',
            priority: 'urgent',
            owner: 'sarah.davis',
            due_date: '2024-12-23',
            created_at: '2024-12-19T16:00:00Z',
            updated_at: '2024-12-21T10:00:00Z',
            source_doc_id: null,
            linked_document_ids: [],
          },
        ] as Task[];
      }
    },
  });

  // Create task mutation
  const createTaskMutation = useMutation({
    mutationFn: async (taskData: any) => {
      try {
        return await api.tasks.createTask(taskData);
      } catch (error) {
        console.error('Failed to create task:', error);
        // Fallback behavior for development
        return { id: Date.now(), ...taskData, status: 'new', created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Update task mutation
  const updateTaskMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Task> }) => {
      try {
        return await api.tasks.updateTask(id, data);
      } catch (error) {
        console.error('Failed to update task:', error);
        // Fallback behavior for development
        return { id, ...data, updated_at: new Date().toISOString() };
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Delete task mutation
  const deleteTaskMutation = useMutation({
    mutationFn: async (id: number) => {
      try {
        return await api.tasks.deleteTask(id);
      } catch (error) {
        console.error('Failed to delete task:', error);
        // Continue even if API fails in development
      }
    },
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
    <div className={cn(
      "h-full flex flex-col bg-background transition-all duration-300",
      selectedTask && "mr-96"
    )}>
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
                  onSelect={(task) => setSelectedTask(task)}
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
                onSelect={(task) => setSelectedTask(task)}
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

      {/* Create/Edit Task Modal */}
      {showCreateModal && (
        <TaskFormModal
          task={editingTask}
          onClose={() => {
            setShowCreateModal(false);
            setEditingTask(null);
          }}
          onSave={async (taskData) => {
            if (editingTask) {
              // Update existing task
              await updateTaskMutation.mutateAsync({ 
                id: editingTask.id, 
                ...taskData 
              });
            } else {
              // Create new task
              await createTaskMutation.mutateAsync(taskData);
            }
            setShowCreateModal(false);
            setEditingTask(null);
          }}
        />
      )}

      {/* Task Detail Panel */}
      <AnimatePresence>
        {selectedTask && (
          <TaskDetailPanel
            task={selectedTask}
            onClose={() => setSelectedTask(null)}
            onEdit={(task) => {
              setEditingTask(task);
              setShowCreateModal(true);
              setSelectedTask(null);
            }}
            onDelete={handleDelete}
            onStatusChange={handleStatusChange}
          />
        )}
      </AnimatePresence>
    </div>
  );
};
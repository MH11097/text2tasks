import React, { useState, useCallback, useMemo } from 'react';
import { Search, Bell, User, Menu, X, Plus, Filter, Grid3X3, List, 
         Calendar, Tag, Users, FileText, MessageCircle, Upload, 
         Download, Eye, Trash2, Send, Paperclip,
         CheckSquare, Clock, AlertCircle, CheckCircle, Pause, Play } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore, useTasks, useTheme } from '@/stores/app-store';
import { api } from '@/services/api';
import { Task, TaskStatus, TaskPriority, User as UserType } from '@/types';

// Local interfaces for the existing component structure
interface QAMessage {
  id: string;
  type: 'question' | 'answer';
  content: string;
  timestamp: string;
  user?: UserType;
  references?: string[];
}

// Utility Components from original
const Button: React.FC<{
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
}> = ({ variant = 'primary', size = 'md', onClick, children, className = '', disabled = false }) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-lg font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-600',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };
  
  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

const Badge: React.FC<{
  variant: 'status' | 'priority' | 'tag';
  value: string;
  className?: string;
}> = ({ variant, value, className = '' }) => {
  const getClasses = () => {
    const base = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
    
    if (variant === 'status') {
      const statusColors = {
        new: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
        todo: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
        in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
        done: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
        blocked: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      };
      return `${base} ${statusColors[value as keyof typeof statusColors]}`;
    }
    
    if (variant === 'priority') {
      const priorityColors = {
        low: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
        medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
        high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
        urgent: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
        critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      };
      return `${base} ${priorityColors[value as keyof typeof priorityColors]}`;
    }
    
    return `${base} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200`;
  };
  
  return <span className={`${getClasses()} ${className}`}>{value}</span>;
};

const Avatar: React.FC<{ user: UserType; size?: 'sm' | 'md' | 'lg' }> = ({ user, size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-6 h-6 text-sm',
    md: 'w-8 h-8 text-base',
    lg: 'w-10 h-10 text-lg'
  };
  
  return (
    <div className={`${sizeClasses[size]} rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center font-medium text-blue-600 dark:text-blue-300`}>
      {user.name?.charAt(0).toUpperCase() || '?'}
    </div>
  );
};

export const TasksPage: React.FC = () => {
  // Store hooks
  const { selectedTaskId, setSelectedTaskId, taskFilters, setTaskFilters } = useTasks();
  const { getEffectiveTheme } = useTheme();
  const isDarkMode = getEffectiveTheme() === 'dark';
  
  // Local state
  const [activeTab, setActiveTab] = useState<'info' | 'documents' | 'qa'>('info');
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [newMessage, setNewMessage] = useState('');

  // Query client
  const queryClient = useQueryClient();

  // Fetch tasks from API
  const { data: tasks = [], isLoading, error } = useQuery({
    queryKey: ['tasks', { status: statusFilter, priority: priorityFilter, search: searchQuery }],
    queryFn: async () => {
      const response = await api.tasks.getTasks({
        status: statusFilter === 'all' ? undefined : statusFilter,
        priority: priorityFilter === 'all' ? undefined : priorityFilter,
        search: searchQuery || undefined
      });
      return response;
    },
    staleTime: 30000, // 30 seconds
  });

  // Get selected task
  const selectedTask = useMemo(() => {
    return tasks.find((task: Task) => task.id === selectedTaskId);
  }, [tasks, selectedTaskId]);

  // Filtered tasks for display
  const filteredTasks = useMemo(() => {
    return tasks.filter((task: Task) => {
      const matchesSearch = task.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          task.description?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
      const matchesPriority = priorityFilter === 'all' || task.priority === priorityFilter;
      
      return matchesSearch && matchesStatus && matchesPriority;
    });
  }, [tasks, searchQuery, statusFilter, priorityFilter]);

  // Event Handlers
  const handleTaskSelect = useCallback((task: Task) => {
    setSelectedTaskId(task.id);
  }, [setSelectedTaskId]);

  const handleSendMessage = useCallback(async () => {
    if (!newMessage.trim() || !selectedTask) return;
    
    try {
      // Send question to AI
      const response = await api.qa.ask({
        question: newMessage,
        context: `Task: ${selectedTask.title}\nDescription: ${selectedTask.description}`
      });
      
      // In a real implementation, you'd update the task's QA history
      console.log('AI Response:', response);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }, [newMessage, selectedTask]);

  // Create task mutation
  const createTaskMutation = useMutation({
    mutationFn: api.tasks.createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Update task mutation
  const updateTaskMutation = useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: Partial<Task> }) =>
      api.tasks.updateTask(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Delete task mutation
  const deleteTaskMutation = useMutation({
    mutationFn: api.tasks.deleteTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setSelectedTaskId(null);
    },
  });

  // Status icons
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'new':
      case 'todo': return <Clock className="w-4 h-4" />;
      case 'in_progress': return <Play className="w-4 h-4" />;
      case 'done': return <CheckCircle className="w-4 h-4" />;
      case 'blocked': return <Pause className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex-1 flex items-center justify-center"
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading tasks...</p>
        </div>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex-1 flex items-center justify-center"
      >
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Failed to load tasks
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Please try refreshing the page.
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex-1 flex h-full"
    >
      {/* Task List */}
      <div className="w-1/3 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Tasks ({filteredTasks.length})
            </h1>
            <Button 
              size="sm" 
              onClick={() => createTaskMutation.mutate({
                title: 'New Task',
                description: 'Task description'
              })}
              disabled={createTaskMutation.isPending}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Task
            </Button>
          </div>
          
          {/* Search */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500 dark:text-gray-400" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {/* Filters */}
          <div className="flex gap-2 mb-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 text-sm rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="new">New</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
              <option value="blocked">Blocked</option>
            </select>
            
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-3 py-1.5 text-sm rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Priority</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex gap-1">
              <Button
                variant={viewMode === 'cards' ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setViewMode('cards')}
                className="p-2"
              >
                <Grid3X3 className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === 'table' ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setViewMode('table')}
                className="p-2"
              >
                <List className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
        
        {/* Task Cards */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          <AnimatePresence>
            {filteredTasks.map((task: Task) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleTaskSelect(task)}
                className={`p-4 rounded-xl border cursor-pointer transition-all hover:shadow-md ${
                  selectedTask?.id === task.id
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(task.status || 'new')}
                    <Badge variant="status" value={task.status || 'new'} />
                  </div>
                  <Badge variant="priority" value={task.priority || 'medium'} />
                </div>
                
                <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">
                  {task.title}
                </h3>
                
                <p className="text-sm mb-3 line-clamp-2 text-gray-600 dark:text-gray-300">
                  {task.description}
                </p>
                
                <div className="flex items-center justify-between mb-3">
                  {task.assignee && <Avatar user={task.assignee} size="sm" />}
                  {task.due_date && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Due: {new Date(task.due_date).toLocaleDateString()}
                    </span>
                  )}
                </div>
                
                {task.tags && task.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {task.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="tag" value={tag} />
                    ))}
                    {task.tags.length > 3 && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        +{task.tags.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Task Detail */}
      <div className="flex-1 flex flex-col">
        {selectedTask ? (
          <motion.div
            key={selectedTask.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex flex-col h-full"
          >
            {/* Task Header */}
            <div className="p-6 border-b bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {selectedTask.title}
                </h1>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm">Edit</Button>
                  <Button 
                    variant="danger" 
                    size="sm"
                    onClick={() => deleteTaskMutation.mutate(selectedTask.id)}
                    disabled={deleteTaskMutation.isPending}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              {/* Tabs */}
              <div className="flex gap-6 border-b border-gray-200 dark:border-gray-700">
                {[
                  { id: 'info', label: 'Task Info', icon: CheckSquare },
                  { id: 'documents', label: 'Documents', icon: FileText, count: 0 },
                  { id: 'qa', label: 'Q&A', icon: MessageCircle, count: 0 },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-2 pb-3 border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    <span className="font-medium">{tab.label}</span>
                    {tab.count !== undefined && (
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        activeTab === tab.id
                          ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {tab.count}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto">
              <AnimatePresence mode="wait">
                {activeTab === 'info' && (
                  <motion.div
                    key="info"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-6 space-y-6"
                  >
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                          Description
                        </label>
                        <textarea
                          value={selectedTask.description || ''}
                          readOnly
                          className="w-full p-3 rounded-lg border bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white resize-none"
                          rows={4}
                        />
                      </div>
                      
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                            Status
                          </label>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(selectedTask.status || 'new')}
                            <Badge variant="status" value={selectedTask.status || 'new'} />
                          </div>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                            Priority
                          </label>
                          <Badge variant="priority" value={selectedTask.priority || 'medium'} />
                        </div>
                        
                        {selectedTask.assignee && (
                          <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                              Assignee
                            </label>
                            <div className="flex items-center gap-2">
                              <Avatar user={selectedTask.assignee} />
                              <span className="text-gray-900 dark:text-white">
                                {selectedTask.assignee.name}
                              </span>
                            </div>
                          </div>
                        )}
                        
                        {selectedTask.due_date && (
                          <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                              Due Date
                            </label>
                            <div className="flex items-center gap-2">
                              <Calendar className="w-4 h-4 text-gray-500" />
                              <span className="text-gray-900 dark:text-white">
                                {new Date(selectedTask.due_date).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {selectedTask.tags && selectedTask.tags.length > 0 && (
                      <div>
                        <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                          Tags
                        </label>
                        <div className="flex flex-wrap gap-2">
                          {selectedTask.tags.map((tag) => (
                            <Badge key={tag} variant="tag" value={tag} />
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}

                {activeTab === 'documents' && (
                  <motion.div
                    key="documents"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-6"
                  >
                    {/* Upload Area */}
                    <div className="border-2 border-dashed rounded-xl p-8 text-center mb-6 border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
                      <Upload className="w-12 h-12 mx-auto mb-4 text-gray-500 dark:text-gray-400" />
                      <p className="text-lg font-medium mb-2 text-gray-900 dark:text-white">
                        Drop files here or click to upload
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Support for PDF, DOC, XLSX, PNG, JPG files up to 10MB
                      </p>
                      <Button className="mt-4">
                        <Upload className="w-4 h-4 mr-2" />
                        Choose Files
                      </Button>
                    </div>

                    {/* Placeholder for future document list */}
                    <div className="text-center py-8">
                      <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400 dark:text-gray-600" />
                      <p className="text-gray-500 dark:text-gray-400">No documents uploaded yet</p>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'qa' && (
                  <motion.div
                    key="qa"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex flex-col h-full"
                  >
                    {/* Placeholder messages */}
                    <div className="flex-1 p-6 space-y-4 overflow-y-auto">
                      <div className="text-center py-8">
                        <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-400 dark:text-gray-600" />
                        <p className="text-gray-500 dark:text-gray-400">No conversations yet</p>
                        <p className="text-sm text-gray-400 dark:text-gray-500">Ask a question to get started</p>
                      </div>
                    </div>

                    {/* Message Input */}
                    <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                      <div className="flex gap-3">
                        <div className="flex-1">
                          <textarea
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            placeholder="Ask a question about this task..."
                            className="w-full p-3 rounded-lg border resize-none bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={2}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSendMessage();
                              }
                            }}
                          />
                        </div>
                        <div className="flex flex-col gap-2">
                          <Button variant="secondary" size="sm" className="p-2">
                            <Paperclip className="w-4 h-4" />
                          </Button>
                          <Button onClick={handleSendMessage} disabled={!newMessage.trim()} className="p-2">
                            <Send className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex-1 flex items-center justify-center"
          >
            <div className="text-center">
              <CheckSquare className="w-16 h-16 mx-auto mb-4 text-gray-400 dark:text-gray-600" />
              <h2 className="text-xl font-semibold mb-2 text-gray-600 dark:text-gray-300">
                Select a task to view details
              </h2>
              <p className="text-gray-500 dark:text-gray-400">
                Choose a task from the list to see its information, documents, and Q&A history.
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};
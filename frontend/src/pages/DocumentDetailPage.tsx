import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  FileText,
  Edit3,
  Save,
  X,
  RefreshCw,
  Download,
  Share,
  Tag,
  Calendar,
  User,
  CheckSquare,
  Clock,
  AlertCircle,
  Loader2,
  Plus,
} from 'lucide-react';

import { api } from '@/services/api';
import { cn } from '@/utils/cn';
import { formatRelativeTime, formatFileSize } from '@/utils/format';
import { MonacoEditor } from '@/components/common/MonacoEditor';

interface Document {
  id: number;
  title: string;
  summary?: string;
  content: string;
  source_type: string;
  created_at: string;
  updated_at: string;
  file_size?: number;
  tags?: string[];
}

interface Task {
  id: number;
  title: string;
  status: 'new' | 'in_progress' | 'blocked' | 'done';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  owner?: string;
  created_at: string;
  abbreviation?: string; // First 2-3 chars of title
}

interface TaskSquareProps {
  task: Task;
  onClick?: () => void;
}

const TaskSquare: React.FC<TaskSquareProps> = ({ task, onClick }) => {
  const statusColors = {
    new: 'bg-gray-100 text-gray-700 border-gray-300',
    in_progress: 'bg-blue-100 text-blue-700 border-blue-300',
    blocked: 'bg-red-100 text-red-700 border-red-300',
    done: 'bg-green-100 text-green-700 border-green-300',
  };

  const getAbbreviation = (title: string) => {
    return title
      .split(' ')
      .slice(0, 2)
      .map(word => word.charAt(0).toUpperCase())
      .join('')
      .substring(0, 3);
  };

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={cn(
        'w-12 h-12 rounded-lg border-2 flex items-center justify-center cursor-pointer transition-all',
        'hover:shadow-md font-bold text-sm',
        statusColors[task.status]
      )}
      title={`${task.title} - ${task.status}`}
    >
      {task.abbreviation || getAbbreviation(task.title)}
    </motion.div>
  );
};

interface TabsProps {
  tabs: Array<{
    id: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    count?: number;
  }>;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onTabChange }) => {
  return (
    <div className="border-b border-border">
      <div className="flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              'flex items-center gap-2 pb-3 pt-1 border-b-2 transition-all',
              activeTab === tab.id
                ? 'border-primary text-primary font-medium'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            )}
          >
            <tab.icon className="h-4 w-4" />
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className={cn(
                'px-2 py-0.5 rounded-full text-xs font-medium',
                activeTab === tab.id
                  ? 'bg-primary/10 text-primary'
                  : 'bg-muted text-muted-foreground'
              )}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [isSyncing, setIsSyncing] = useState(false);

  // Fetch document details
  const { data: document, isLoading, error } = useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      // Mock data for now - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate loading
      return {
        id: parseInt(id!),
        title: 'Project Requirements Document',
        summary: 'Comprehensive requirements for the new AI Work OS project including functional and non-functional requirements, technical specifications, and implementation guidelines.',
        content: `# Project Requirements Document

## Overview
This document outlines the comprehensive requirements for the AI Work OS project, a personal productivity tool designed to automate work management from raw text input.

## Functional Requirements

### Core Features
1. **Text Processing**: Automated extraction and categorization of tasks from unstructured text
2. **Task Management**: Create, update, delete, and track tasks with status management
3. **Document Storage**: Store and organize documents with full-text search capabilities
4. **Q&A System**: AI-powered question-answering system with contextual understanding
5. **User Interface**: Modern, responsive web interface with dark/light theme support

### Technical Requirements
- **Backend**: FastAPI with SQLite database
- **Frontend**: React 18 with TypeScript and Tailwind CSS
- **AI Integration**: OpenAI GPT models for text processing and Q&A
- **Performance**: Sub-2 second response times for most operations
- **Security**: Input validation, rate limiting, and secure API endpoints

## Non-Functional Requirements

### Usability
- Intuitive user interface with minimal learning curve
- Mobile-responsive design
- Keyboard shortcuts for power users
- Accessibility compliance (WCAG 2.1 AA)

### Performance
- Page load times under 3 seconds
- API response times under 2 seconds
- Support for documents up to 10MB
- Concurrent user support (minimum 100 users)

### Reliability
- 99.5% uptime availability
- Automated backups every 24 hours
- Error handling and graceful degradation
- Transaction rollback capabilities

## Implementation Guidelines

### Development Approach
1. Clean Architecture pattern implementation
2. Test-driven development (TDD)
3. Continuous integration/deployment (CI/CD)
4. Code review process for all changes

### Quality Assurance
- Unit test coverage minimum 80%
- Integration tests for all API endpoints
- End-to-end testing for critical user flows
- Performance testing under load conditions

### Deployment
- Docker containerization
- Environment-specific configurations
- Rolling deployment strategy
- Health checks and monitoring`,
        source_type: 'Document',
        created_at: '2024-12-20T10:00:00Z',
        updated_at: '2024-12-21T15:30:00Z',
        file_size: 2048576,
        tags: ['project', 'requirements', 'ai', 'architecture'],
      } as Document;
    },
    enabled: !!id,
  });

  // Fetch related tasks (mock data)
  const { data: relatedTasks = [] } = useQuery({
    queryKey: ['document-tasks', id],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 300));
      return [
        {
          id: 1,
          title: 'Implement user authentication',
          status: 'in_progress' as const,
          priority: 'high' as const,
          owner: 'John Doe',
          created_at: '2024-12-20T09:00:00Z',
        },
        {
          id: 2,
          title: 'Set up database schema',
          status: 'done' as const,
          priority: 'high' as const,
          owner: 'Jane Smith',
          created_at: '2024-12-19T14:00:00Z',
        },
        {
          id: 3,
          title: 'Create API documentation',
          status: 'new' as const,
          priority: 'medium' as const,
          owner: 'Bob Wilson',
          created_at: '2024-12-21T11:00:00Z',
        },
        {
          id: 4,
          title: 'Implement file upload feature',
          status: 'blocked' as const,
          priority: 'medium' as const,
          owner: 'Alice Johnson',
          created_at: '2024-12-20T16:00:00Z',
        },
        {
          id: 5,
          title: 'Add search functionality',
          status: 'new' as const,
          priority: 'low' as const,
          owner: 'Charlie Brown',
          created_at: '2024-12-21T10:00:00Z',
        },
      ] as Task[];
    },
    enabled: !!id,
  });

  // LLM Sync mutation
  const syncMutation = useMutation({
    mutationFn: async () => {
      // Mock API call - replace with actual implementation
      await new Promise(resolve => setTimeout(resolve, 3000));
      return { success: true, message: 'Document synchronized successfully' };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document', id] });
      setIsSyncing(false);
    },
    onError: () => {
      setIsSyncing(false);
    },
  });

  useEffect(() => {
    if (document && !isEditing) {
      setEditedContent(document.content);
    }
  }, [document, isEditing]);

  const handleBack = () => {
    navigate('/documents');
  };

  const handleEdit = () => {
    setIsEditing(true);
    setEditedContent(document?.content || '');
  };

  const handleSave = () => {
    // TODO: Implement save functionality
    setIsEditing(false);
    console.log('Save content:', editedContent);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedContent(document?.content || '');
  };

  const handleSync = () => {
    setIsSyncing(true);
    syncMutation.mutate();
  };

  const handleTaskClick = (taskId: number) => {
    // TODO: Navigate to task detail or open task modal
    console.log('Open task:', taskId);
  };

  const tabs = [
    {
      id: 'overview',
      label: 'Overview',
      icon: FileText,
    },
    {
      id: 'tasks',
      label: 'Related Tasks',
      icon: CheckSquare,
      count: relatedTasks.length,
    },
    {
      id: 'content',
      label: 'Raw Content',
      icon: Edit3,
    },
  ];

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">Document not found</h3>
          <p className="text-muted-foreground mb-4">The requested document could not be loaded.</p>
          <button
            onClick={handleBack}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="h-full flex flex-col bg-background"
    >
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border bg-card/50">
        <div className="px-6 py-4">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBack}
                className="p-2 rounded-lg hover:bg-muted transition-colors"
                title="Back to Documents"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-foreground">{document.title}</h1>
                <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    Created {formatRelativeTime(document.created_at)}
                  </span>
                  {document.file_size && (
                    <span>{formatFileSize(document.file_size)}</span>
                  )}
                  <span className="px-2 py-1 bg-secondary rounded text-secondary-foreground text-xs">
                    {document.source_type}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {!isEditing ? (
                <>
                  <button
                    onClick={handleEdit}
                    className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors"
                  >
                    <Edit3 className="h-4 w-4" />
                    Edit
                  </button>
                  <button
                    onClick={handleSync}
                    disabled={isSyncing}
                    className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  >
                    {isSyncing ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                    {isSyncing ? 'Syncing...' : 'LLM Sync'}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleCancel}
                    className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors"
                  >
                    <X className="h-4 w-4" />
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                  >
                    <Save className="h-4 w-4" />
                    Save Changes
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Tags */}
          {document.tags && document.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {document.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-secondary text-secondary-foreground rounded-full text-xs"
                >
                  <Tag className="h-3 w-3" />
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Tabs */}
          <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-6">
          <AnimatePresence mode="wait">
            {activeTab === 'overview' && (
              <motion.div
                key="overview"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                {/* Summary */}
                {document.summary && (
                  <div className="bg-card border border-border rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-foreground mb-3">Summary</h3>
                    <p className="text-muted-foreground leading-relaxed">{document.summary}</p>
                  </div>
                )}

                {/* Quick Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                        <CheckSquare className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Related Tasks</p>
                        <p className="text-2xl font-bold text-foreground">{relatedTasks.length}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                        <Clock className="h-5 w-5 text-green-600 dark:text-green-400" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Last Updated</p>
                        <p className="text-sm font-medium text-foreground">{formatRelativeTime(document.updated_at)}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                        <Tag className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Tags</p>
                        <p className="text-2xl font-bold text-foreground">{document.tags?.length || 0}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'tasks' && (
              <motion.div
                key="tasks"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4">Tasks Using This Document</h3>
                  
                  {relatedTasks.length > 0 ? (
                    <>
                      {/* Task Squares Visualization */}
                      <div className="mb-6">
                        <p className="text-sm text-muted-foreground mb-3">Task Status Overview</p>
                        <div className="flex flex-wrap gap-3">
                          {relatedTasks.map((task) => (
                            <TaskSquare
                              key={task.id}
                              task={task}
                              onClick={() => handleTaskClick(task.id)}
                            />
                          ))}
                        </div>
                      </div>

                      {/* Task List */}
                      <div className="space-y-3">
                        {relatedTasks.map((task) => (
                          <motion.div
                            key={task.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex items-center justify-between p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                            onClick={() => handleTaskClick(task.id)}
                          >
                            <div className="flex items-center gap-3">
                              <TaskSquare task={task} />
                              <div>
                                <h4 className="font-medium text-foreground">{task.title}</h4>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                  <span>Status: {task.status}</span>
                                  {task.owner && (
                                    <>
                                      <span>•</span>
                                      <span>Owner: {task.owner}</span>
                                    </>
                                  )}
                                  {task.priority && (
                                    <>
                                      <span>•</span>
                                      <span>Priority: {task.priority}</span>
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {formatRelativeTime(task.created_at)}
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8">
                      <CheckSquare className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                      <p className="text-muted-foreground">No tasks are currently using this document</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === 'content' && (
              <motion.div
                key="content"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-4"
              >
                <div className="bg-card border border-border rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-foreground">Raw Content</h3>
                    {!isEditing && (
                      <p className="text-sm text-muted-foreground">
                        Edit this content to automatically update the summary via LLM processing
                      </p>
                    )}
                  </div>
                  
                  {isEditing ? (
                    <div className="border border-border rounded-lg overflow-hidden">
                      <MonacoEditor
                        value={editedContent}
                        onChange={(value) => setEditedContent(value || '')}
                        language="markdown"
                        height={400}
                        placeholder="Enter document content..."
                      />
                    </div>
                  ) : (
                    <div className="border border-border rounded-lg overflow-hidden">
                      <MonacoEditor
                        value={document.content}
                        onChange={() => {}}
                        language="markdown"
                        height={400}
                        readOnly
                      />
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};
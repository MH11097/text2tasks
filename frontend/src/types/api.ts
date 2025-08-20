// API Response Types
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  success?: boolean;
}

export interface ApiError {
  detail: string;
  type?: string;
  code?: string;
}

// User Types
export interface User {
  id: number | string;
  name: string;
  email?: string;
  avatar?: string;
  role?: string;
}

// Task Types  
export interface Task {
  id: number;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  progress_percentage?: number;
  created_at: string;
  updated_at?: string;
  due_date?: string;
  owner?: string;
  assignee?: User;
  task_code?: string;
  parent_task_id?: number;
  task_level?: number;
  children?: Task[];
  tags?: string[];
}

export type TaskStatus = 'new' | 'in_progress' | 'done' | 'blocked';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface TaskCreateRequest {
  title: string;
  description?: string;
  priority?: TaskPriority;
  due_date?: string;
  owner?: string;
  parent_task_id?: number;
}

export interface TaskUpdateRequest {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  progress_percentage?: number;
  due_date?: string;
  owner?: string;
}

export interface TaskHierarchyResponse {
  task: Task;
  ancestors?: Task[];
  descendants?: Task[];
}

// Resource Types
export interface Resource {
  id: number;
  text: string;
  summary?: string;
  source: string;
  source_type: string;
  created_at: string;
  assignment_status: ResourceAssignmentStatus;
  task_count?: number;
  assigned_at?: string;
  assigned_by?: string;
  inherited?: boolean;
}

export type ResourceAssignmentStatus = 'unassigned' | 'assigned' | 'archived';

export interface ResourceAssignRequest {
  task_ids: number[];
  assigned_by?: string;
}

export interface BulkResourceAssignRequest {
  resource_ids: number[];
  assigned_by?: string;
}

// Document/Ingest Types
export interface IngestRequest {
  text: string;
  source?: string;
  source_type?: string;
}

export interface IngestResponse {
  document_id: number;
  extracted_tasks: Task[];
  summary: string;
  created_embeddings: boolean;
}

// Q&A Types
export interface AskRequest {
  question: string;
  scope?: QAScope;
  top_k?: number;
}

export type QAScope = 'self' | 'subtasks' | 'tree' | 'inherit';

export interface AskResponse {
  answer: string;
  task_context?: {
    task_code: string;
    task_title: string;
    scope: string;
  };
  context_summary?: {
    documents_used: number;
    task_specific: number;
    inherited: number;
    general: number;
  };
  suggested_next_steps?: string[];
  multi_task_context?: {
    task_codes: string[];
    primary_task: string;
    total_tasks: number;
  };
}

export interface ContextPreviewResponse {
  task: Task;
  scope: string;
  available_resources: {
    total: number;
    task_specific: number;
    inherited: number;
    general: number;
  };
  suggested_scopes: Array<{
    name: string;
    description: string;
  }>;
}

// System Status Types
export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'down';
  database: 'connected' | 'disconnected';
  tasks_summary: {
    total: number;
    new: number;
    in_progress: number;
    done: number;
    blocked: number;
  };
  recent_activity: string;
}

export interface ResourceStats {
  resource_assignment: {
    total_resources: number;
    resources_by_status: {
      assigned: number;
      unassigned: number;
      archived: number;
    };
  };
  task_hierarchy: {
    total_tasks: number;
    root_tasks: number;
    max_hierarchy_depth: number;
  };
}

// User Types (for future enhancement)
export interface User {
  id: string;
  name: string;
  email?: string;
  avatar?: string;
  role: UserRole;
}

export type UserRole = 'admin' | 'manager' | 'developer' | 'viewer';

// Pagination Types
export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// Filter Types
export interface TaskFilters {
  status?: TaskStatus[];
  priority?: TaskPriority[];
  owner?: string[];
  due_date_from?: string;
  due_date_to?: string;
  search?: string;
  parent_task_id?: number;
}

export interface ResourceFilters {
  assignment_status?: ResourceAssignmentStatus[];
  source_type?: string[];
  search?: string;
  task_id?: number;
}

// File Upload Types
export interface FileUploadRequest {
  file: File;
  description?: string;
  task_id?: number;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// WebSocket Types (for future real-time features)
export interface WebSocketMessage {
  type: 'task_updated' | 'resource_assigned' | 'user_activity' | 'system_notification';
  payload: unknown;
  timestamp: string;
  user_id?: string;
}

export interface TaskUpdateMessage {
  task_id: number;
  changes: Partial<Task>;
  updated_by?: string;
}

// UI State Types
export interface AppState {
  theme: 'light' | 'dark' | 'system';
  sidebarCollapsed: boolean;
  selectedTaskId?: number;
  selectedResourceIds: Set<number>;
  currentView: AppView;
  isLoading: boolean;
  error?: string;
}

export type AppView = 'dashboard' | 'tasks' | 'resources' | 'qa' | 'settings';

// Form Types
export interface FormState<T> {
  data: T;
  errors: Partial<Record<keyof T, string>>;
  isSubmitting: boolean;
  isValid: boolean;
}

// Notification Types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    callback: () => void;
  };
}

// Search Types
export interface SearchResult {
  type: 'task' | 'resource' | 'document';
  id: number;
  title: string;
  description?: string;
  relevance: number;
  highlights?: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  took: number;
}

// Export all types
export type * from './api';
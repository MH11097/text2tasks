import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import logger from './logger';
import type {
  ApiResponse,
  ApiError,
  Task,
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskHierarchyResponse,
  Resource,
  ResourceAssignRequest,
  BulkResourceAssignRequest,
  IngestRequest,
  IngestResponse,
  AskRequest,
  AskResponse,
  ContextPreviewResponse,
  SystemStatus,
  ResourceStats,
  PaginationParams,
  TaskFilters,
  ResourceFilters,
  PaginatedResponse,
} from '@/types';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance with default configuration
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor for adding auth headers, request ID, etc.
  client.interceptors.request.use(
    (config) => {
      // Generate request ID for tracking
      const requestId = crypto.randomUUID();
      config.headers['X-Request-ID'] = requestId;
      
      // Store request metadata for logging
      config.metadata = { 
        startTime: Date.now(),
        requestId 
      };
      
      // Add API key if available
      const apiKey = import.meta.env.VITE_API_KEY;
      if (apiKey) {
        config.headers['X-API-Key'] = apiKey;
      }
      
      // Add timestamp
      config.headers['X-Timestamp'] = new Date().toISOString();
      
      // Log the request
      logger.apiRequest(
        config.method?.toUpperCase() || 'GET',
        config.url || '',
        requestId,
        {
          params: config.params,
          headers: config.headers
        }
      );
      
      return config;
    },
    (error) => {
      logger.error('API request configuration error', {
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack
        },
        component: 'api',
        action: 'request_config_error'
      });
      return Promise.reject(error);
    }
  );

  // Response interceptor for handling common response patterns
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      const config = response.config;
      const requestId = config.metadata?.requestId;
      const duration = Date.now() - (config.metadata?.startTime || Date.now());

      // Log successful response
      logger.apiResponse(
        config.method?.toUpperCase() || 'GET',
        config.url || '',
        response.status,
        duration,
        requestId,
        {
          responseSize: JSON.stringify(response.data).length,
          responseHeaders: response.headers
        }
      );

      // Log successful requests in development console
      if (import.meta.env.DEV) {
        console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url}`, {
          status: response.status,
          data: response.data,
          requestId: response.headers['x-request-id'],
          duration: `${duration}ms`
        });
      }
      return response;
    },
    (error: AxiosError<ApiError>) => {
      const config = error.config;
      const requestId = config?.metadata?.requestId;
      const duration = Date.now() - (config?.metadata?.startTime || Date.now());
      
      // Enhanced error handling
      const errorData = error.response?.data;
      const errorMessage = errorData?.detail || error.message || 'An unexpected error occurred';
      
      // Log error response
      logger.apiResponse(
        config?.method?.toUpperCase() || 'GET',
        config?.url || '',
        error.response?.status || 0,
        duration,
        requestId,
        {
          error: {
            name: error.name,
            message: error.message,
            stack: error.stack
          },
          errorCode: error.code,
          responseData: error.response?.data
        }
      );
      
      // Log errors in development console
      if (import.meta.env.DEV) {
        console.error(`❌ ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
          status: error.response?.status,
          message: errorMessage,
          data: errorData,
          requestId: error.response?.headers['x-request-id'],
          duration: `${duration}ms`
        });
      }
      
      // Create enhanced error object
      const enhancedError = new Error(errorMessage) as Error & {
        status?: number;
        code?: string;
        type?: string;
        requestId?: string;
      };
      
      enhancedError.status = error.response?.status;
      enhancedError.code = errorData?.code;
      enhancedError.type = errorData?.type;
      enhancedError.requestId = error.response?.headers['x-request-id'];
      
      return Promise.reject(enhancedError);
    }
  );

  return client;
};

// Create the API client instance
const apiClient = createApiClient();

// Generic API request function with type safety
async function apiRequest<T>(
  config: AxiosRequestConfig
): Promise<T> {
  try {
    const response = await apiClient.request<ApiResponse<T>>(config);
    return response.data.data || response.data;
  } catch (error) {
    throw error;
  }
}

// Health Check API
export const healthApi = {
  check: async (): Promise<{ status: string }> => {
    return apiRequest({
      method: 'GET',
      url: '/v1/healthz',
    });
  },
};

// System Status API
export const statusApi = {
  getStatus: async (): Promise<SystemStatus> => {
    return apiRequest({
      method: 'GET',
      url: '/v1/status',
    });
  },
  
  getResourceStats: async (): Promise<ResourceStats> => {
    return apiRequest({
      method: 'GET',
      url: '/v1/resources/stats',
    });
  },
};

// Task Management API
export const taskApi = {
  // Get all tasks
  getTasks: async (filters?: TaskFilters, pagination?: PaginationParams): Promise<Task[]> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }
    
    if (pagination) {
      Object.entries(pagination).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    return apiRequest({
      method: 'GET',
      url: `/v1/tasks${params.toString() ? `?${params.toString()}` : ''}`,
    });
  },

  // Get task by ID
  getTask: async (id: number): Promise<Task> => {
    return apiRequest({
      method: 'GET',
      url: `/v1/tasks/${id}`,
    });
  },

  // Create new task
  createTask: async (data: TaskCreateRequest): Promise<Task> => {
    return apiRequest({
      method: 'POST',
      url: '/v1/tasks',
      data,
    });
  },

  // Update task
  updateTask: async (id: number, data: TaskUpdateRequest): Promise<Task> => {
    return apiRequest({
      method: 'PATCH',
      url: `/v1/tasks/${id}`,
      data,
    });
  },

  // Delete task
  deleteTask: async (id: number): Promise<void> => {
    return apiRequest({
      method: 'DELETE',
      url: `/v1/tasks/${id}`,
    });
  },
};

// Task Hierarchy API
export const hierarchyApi = {
  // Get task tree
  getTaskTree: async (): Promise<Task[]> => {
    return apiRequest({
      method: 'GET',
      url: '/hierarchy/tree',
    });
  },

  // Get task by code with hierarchy context
  getTaskByCode: async (taskCode: string, includeContext = true): Promise<TaskHierarchyResponse> => {
    return apiRequest({
      method: 'GET',
      url: `/hierarchy/tasks/code/${taskCode}?include_context=${includeContext}`,
    });
  },

  // Create hierarchical task
  createHierarchicalTask: async (data: TaskCreateRequest): Promise<Task> => {
    return apiRequest({
      method: 'POST',
      url: '/hierarchy/tasks',
      data,
    });
  },

  // Move task in hierarchy
  moveTask: async (taskId: number, newParentId: number | null): Promise<Task> => {
    return apiRequest({
      method: 'PUT',
      url: `/hierarchy/tasks/${taskId}/move`,
      data: { new_parent_id: newParentId },
    });
  },
};

// Resource Management API
export const resourceApi = {
  // Get all resources
  getResources: async (filters?: ResourceFilters, pagination?: PaginationParams): Promise<Resource[]> => {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }
    
    if (pagination) {
      Object.entries(pagination).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    return apiRequest({
      method: 'GET',
      url: `/resources${params.toString() ? `?${params.toString()}` : ''}`,
    });
  },

  // Get resource by ID
  getResource: async (id: number): Promise<Resource> => {
    return apiRequest({
      method: 'GET',
      url: `/resources/${id}`,
    });
  },

  // Get resources for a task
  getTaskResources: async (taskId: number, includeInherited = true): Promise<Resource[]> => {
    return apiRequest({
      method: 'GET',
      url: `/resources/tasks/${taskId}?include_inherited=${includeInherited}`,
    });
  },

  // Get tasks for a resource
  getResourceTasks: async (resourceId: number): Promise<Task[]> => {
    return apiRequest({
      method: 'GET',
      url: `/resources/${resourceId}/tasks`,
    });
  },

  // Assign resource to tasks
  assignResource: async (resourceId: number, data: ResourceAssignRequest): Promise<void> => {
    return apiRequest({
      method: 'POST',
      url: `/resources/${resourceId}/assign`,
      data,
    });
  },

  // Bulk assign resources to task
  bulkAssignResources: async (taskId: number, data: BulkResourceAssignRequest): Promise<void> => {
    return apiRequest({
      method: 'POST',
      url: `/resources/tasks/${taskId}/assign`,
      data,
    });
  },

  // Unassign resource from task
  unassignResource: async (resourceId: number, taskId: number): Promise<void> => {
    return apiRequest({
      method: 'DELETE',
      url: `/resources/${resourceId}/tasks/${taskId}`,
    });
  },

  // Archive resources
  archiveResources: async (resourceIds: number[]): Promise<void> => {
    return apiRequest({
      method: 'PUT',
      url: '/resources/bulk/archive',
      data: resourceIds,
    });
  },

  // Unarchive resources
  unarchiveResources: async (resourceIds: number[]): Promise<void> => {
    return apiRequest({
      method: 'PUT',
      url: '/resources/bulk/unarchive',
      data: resourceIds,
    });
  },
};

// Document Ingestion API
export const ingestApi = {
  // Ingest document
  ingestDocument: async (data: IngestRequest): Promise<IngestResponse> => {
    return apiRequest({
      method: 'POST',
      url: '/v1/ingest',
      data,
    });
  },

  // Upload file (for future file upload support)
  uploadFile: async (file: File, onProgress?: (progress: number) => void): Promise<IngestResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    return apiRequest({
      method: 'POST',
      url: '/v1/ingest/file',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  },
};

// Q&A API
export const qaApi = {
  // General Q&A
  ask: async (data: AskRequest): Promise<AskResponse> => {
    return apiRequest({
      method: 'POST',
      url: '/v1/ask',
      data,
    });
  },

  // Task-specific Q&A
  askTaskContext: async (taskCode: string, data: AskRequest): Promise<AskResponse> => {
    return apiRequest({
      method: 'POST',
      url: `/ask/task/${taskCode}`,
      data,
    });
  },

  // Get context preview for task
  getTaskContext: async (taskCode: string, scope?: string): Promise<ContextPreviewResponse> => {
    const params = scope ? `?scope=${scope}` : '';
    return apiRequest({
      method: 'GET',
      url: `/ask/task/${taskCode}/context${params}`,
    });
  },

  // Multi-task contextual Q&A
  askMultiTaskContext: async (taskCodes: string[], data: AskRequest): Promise<AskResponse> => {
    return apiRequest({
      method: 'POST',
      url: '/ask/contextual',
      data: {
        ...data,
        task_codes: taskCodes,
      },
    });
  },
};

// Search API (for future full-text search)
export const searchApi = {
  search: async (query: string, filters?: { type?: string[]; limit?: number }): Promise<any> => {
    const params = new URLSearchParams({ q: query });
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }
    
    return apiRequest({
      method: 'GET',
      url: `/search?${params.toString()}`,
    });
  },
};

// Utility functions
export const apiUtils = {
  // Test API connectivity
  testConnection: async (): Promise<boolean> => {
    try {
      await healthApi.check();
      return true;
    } catch {
      return false;
    }
  },

  // Cancel all pending requests
  cancelAllRequests: () => {
    // Implementation would depend on request tracking
    console.log('Cancelling all pending requests...');
  },

  // Get API base URL
  getBaseUrl: () => API_BASE_URL,

  // Retry failed request
  retry: async <T>(
    requestFn: () => Promise<T>,
    maxRetries = 3,
    delay = 1000
  ): Promise<T> => {
    let lastError: Error;
    
    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error as Error;
        
        if (i === maxRetries) {
          break;
        }
        
        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
    
    throw lastError!;
  },
};

// Export main API object
export const api = {
  health: healthApi,
  status: statusApi,
  tasks: taskApi,
  hierarchy: hierarchyApi,
  resources: resourceApi,
  ingest: ingestApi,
  qa: qaApi,
  search: searchApi,
  utils: apiUtils,
};

export default api;
/**
 * API request/response interceptor for logging
 */

import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import logger from '../services/logger';

// Request interceptor
axios.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Add request ID to headers
    if (config.headers) {
      config.headers['X-Request-ID'] = requestId;
    }

    // Store request start time
    config.metadata = { 
      ...config.metadata, 
      startTime: Date.now(),
      requestId 
    };

    // Log the request
    logger.apiRequest(
      config.method?.toUpperCase() || 'GET',
      config.url || '',
      requestId,
      {
        params: config.params,
        data: config.data,
        headers: config.headers
      }
    );

    return config;
  },
  (error: AxiosError) => {
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

// Response interceptor
axios.interceptors.response.use(
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

    return response;
  },
  (error: AxiosError) => {
    const config = error.config;
    const requestId = config?.metadata?.requestId;
    const duration = Date.now() - (config?.metadata?.startTime || Date.now());

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

    return Promise.reject(error);
  }
);

// Extend AxiosRequestConfig to include metadata
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      startTime: number;
      requestId: string;
    };
  }
}

export default axios;
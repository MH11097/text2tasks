/**
 * Frontend logging service with rotation and storage management
 */

export enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  DEBUG = 'debug'
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, any>;
  userId?: string;
  sessionId?: string;
  requestId?: string;
  component?: string;
  action?: string;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
}

interface LoggerConfig {
  maxEntries: number;
  maxSizeBytes: number;
  enableConsole: boolean;
  enableStorage: boolean;
  storageKey: string;
  levels: LogLevel[];
}

class FrontendLogger {
  private config: LoggerConfig;
  private sessionId: string;
  private userId?: string;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      maxEntries: 1000,
      maxSizeBytes: 5 * 1024 * 1024, // 5MB
      enableConsole: process.env.NODE_ENV === 'development',
      enableStorage: true,
      storageKey: 'app_logs',
      levels: [LogLevel.ERROR, LogLevel.WARN, LogLevel.INFO],
      ...config
    };

    this.sessionId = this.generateSessionId();
    this.setupErrorHandlers();
    this.cleanupOldLogs();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupErrorHandlers(): void {
    // Global error handler
    window.addEventListener('error', (event) => {
      this.error('Global error caught', {
        error: {
          name: event.error?.name || 'Error',
          message: event.error?.message || event.message,
          stack: event.error?.stack,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        },
        component: 'global',
        action: 'error_handler'
      });
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.error('Unhandled promise rejection', {
        error: {
          name: 'UnhandledPromiseRejection',
          message: event.reason?.message || String(event.reason),
          stack: event.reason?.stack
        },
        component: 'global',
        action: 'promise_rejection'
      });
    });
  }

  setUserId(userId: string): void {
    this.userId = userId;
  }

  error(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.ERROR, message, context);
  }

  warn(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, context);
  }

  info(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, context);
  }

  debug(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  // Specific logging methods for common scenarios
  apiRequest(method: string, url: string, requestId?: string, context?: Record<string, any>): void {
    this.info(`API ${method} ${url}`, {
      ...context,
      requestId,
      component: 'api',
      action: 'request',
      method,
      url
    });
  }

  apiResponse(method: string, url: string, status: number, duration: number, requestId?: string, context?: Record<string, any>): void {
    const level = status >= 400 ? LogLevel.ERROR : LogLevel.INFO;
    this.log(level, `API ${method} ${url} - ${status} (${duration}ms)`, {
      ...context,
      requestId,
      component: 'api',
      action: 'response',
      method,
      url,
      status,
      duration
    });
  }

  userAction(action: string, component: string, context?: Record<string, any>): void {
    this.info(`User action: ${action}`, {
      ...context,
      component,
      action,
      event_type: 'user_action'
    });
  }

  pageView(page: string, context?: Record<string, any>): void {
    this.info(`Page view: ${page}`, {
      ...context,
      component: 'navigation',
      action: 'page_view',
      page,
      event_type: 'navigation'
    });
  }

  performanceMetric(metric: string, value: number, unit: string, context?: Record<string, any>): void {
    this.info(`Performance: ${metric} = ${value}${unit}`, {
      ...context,
      component: 'performance',
      action: 'metric',
      metric,
      value,
      unit,
      event_type: 'performance'
    });
  }

  private log(level: LogLevel, message: string, context?: Record<string, any>): void {
    // Check if this log level is enabled
    if (!this.config.levels.includes(level)) {
      return;
    }

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
      userId: this.userId,
      sessionId: this.sessionId,
      requestId: context?.requestId,
      component: context?.component,
      action: context?.action,
      error: context?.error
    };

    // Console logging
    if (this.config.enableConsole) {
      this.logToConsole(entry);
    }

    // Storage logging
    if (this.config.enableStorage) {
      this.logToStorage(entry);
    }
  }

  private logToConsole(entry: LogEntry): void {
    const { level, message, context } = entry;
    const consoleMethod = level === LogLevel.DEBUG ? 'debug' : level;
    
    if (context) {
      console[consoleMethod](`[${entry.timestamp}] ${message}`, context);
    } else {
      console[consoleMethod](`[${entry.timestamp}] ${message}`);
    }
  }

  private logToStorage(entry: LogEntry): void {
    try {
      const existingLogs = this.getStoredLogs();
      existingLogs.push(entry);

      // Check size and rotate if necessary
      const serializedLogs = JSON.stringify(existingLogs);
      if (serializedLogs.length > this.config.maxSizeBytes || existingLogs.length > this.config.maxEntries) {
        this.rotateLogs(existingLogs);
      } else {
        localStorage.setItem(this.config.storageKey, serializedLogs);
      }
    } catch (error) {
      // Storage might be full or unavailable
      console.warn('Failed to write logs to localStorage:', error);
    }
  }

  private getStoredLogs(): LogEntry[] {
    try {
      const stored = localStorage.getItem(this.config.storageKey);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.warn('Failed to read logs from localStorage:', error);
      return [];
    }
  }

  private rotateLogs(logs: LogEntry[]): void {
    // Keep only the most recent logs (50% of max entries)
    const keepCount = Math.floor(this.config.maxEntries * 0.5);
    const recentLogs = logs.slice(-keepCount);

    try {
      localStorage.setItem(this.config.storageKey, JSON.stringify(recentLogs));
      this.info('Log rotation completed', {
        component: 'logger',
        action: 'rotation',
        originalCount: logs.length,
        keptCount: recentLogs.length
      });
    } catch (error) {
      console.warn('Failed to rotate logs:', error);
      // If rotation fails, clear all logs to prevent storage issues
      localStorage.removeItem(this.config.storageKey);
    }
  }

  private cleanupOldLogs(): void {
    const logs = this.getStoredLogs();
    const oneWeekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    
    const recentLogs = logs.filter(log => {
      return new Date(log.timestamp).getTime() > oneWeekAgo;
    });

    if (recentLogs.length !== logs.length) {
      try {
        localStorage.setItem(this.config.storageKey, JSON.stringify(recentLogs));
        this.info('Old logs cleaned up', {
          component: 'logger',
          action: 'cleanup',
          removedCount: logs.length - recentLogs.length
        });
      } catch (error) {
        console.warn('Failed to cleanup old logs:', error);
      }
    }
  }

  // Export logs for debugging or sending to server
  exportLogs(): LogEntry[] {
    return this.getStoredLogs();
  }

  clearLogs(): void {
    localStorage.removeItem(this.config.storageKey);
    this.info('Logs cleared manually', {
      component: 'logger',
      action: 'clear'
    });
  }

  // Get logs by level or component
  getLogs(filters?: {
    level?: LogLevel;
    component?: string;
    since?: Date;
    limit?: number;
  }): LogEntry[] {
    let logs = this.getStoredLogs();

    if (filters) {
      if (filters.level) {
        logs = logs.filter(log => log.level === filters.level);
      }
      if (filters.component) {
        logs = logs.filter(log => log.component === filters.component);
      }
      if (filters.since) {
        logs = logs.filter(log => new Date(log.timestamp) >= filters.since!);
      }
      if (filters.limit) {
        logs = logs.slice(-filters.limit);
      }
    }

    return logs;
  }

  // Send logs to server (for error reporting)
  async sendLogsToServer(levels: LogLevel[] = [LogLevel.ERROR], apiEndpoint = '/api/v1/logs'): Promise<void> {
    const logsToSend = this.getStoredLogs().filter(log => levels.includes(log.level));
    
    if (logsToSend.length === 0) {
      return;
    }

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          logs: logsToSend,
          sessionId: this.sessionId,
          userId: this.userId,
          timestamp: new Date().toISOString()
        })
      });

      if (response.ok) {
        this.info('Logs sent to server successfully', {
          component: 'logger',
          action: 'send_logs',
          count: logsToSend.length
        });
      } else {
        throw new Error(`Server responded with status ${response.status}`);
      }
    } catch (error) {
      this.error('Failed to send logs to server', {
        error: {
          name: error instanceof Error ? error.name : 'Error',
          message: error instanceof Error ? error.message : 'Unknown error'
        },
        component: 'logger',
        action: 'send_logs_error'
      });
    }
  }
}

// Create singleton instance
const logger = new FrontendLogger({
  enableConsole: process.env.NODE_ENV === 'development',
  levels: process.env.NODE_ENV === 'development' 
    ? [LogLevel.ERROR, LogLevel.WARN, LogLevel.INFO, LogLevel.DEBUG]
    : [LogLevel.ERROR, LogLevel.WARN, LogLevel.INFO]
});

export default logger;
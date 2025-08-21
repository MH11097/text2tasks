import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { ThemeMode, AppView, Notification } from '@/types';

// Theme state interface
interface ThemeState {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
  getEffectiveTheme: () => 'light' | 'dark';
}

// UI state interface
interface UIState {
  sidebarCollapsed: boolean;
  currentView: AppView;
  isLoading: boolean;
  error: string | null;
  notifications: Notification[];
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  setCurrentView: (view: AppView) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

// Task state interface
interface TaskState {
  selectedTaskId: number | null;
  selectedTaskIds: Set<number>;
  taskFilters: {
    status?: string[];
    priority?: string[];
    owner?: string[];
    search?: string;
  };
  setSelectedTaskId: (id: number | null) => void;
  toggleTaskSelection: (id: number) => void;
  setTaskSelection: (ids: Set<number>) => void;
  clearTaskSelection: () => void;
  setTaskFilters: (filters: TaskState['taskFilters']) => void;
  updateTaskFilter: (key: string, value: any) => void;
}

// Resource state interface
interface ResourceState {
  selectedResourceIds: Set<number>;
  resourceFilters: {
    assignment_status?: string[];
    source_type?: string[];
    search?: string;
  };
  toggleResourceSelection: (id: number) => void;
  setResourceSelection: (ids: Set<number>) => void;
  clearResourceSelection: () => void;
  setResourceFilters: (filters: ResourceState['resourceFilters']) => void;
  updateResourceFilter: (key: string, value: any) => void;
}

// Search state interface
interface SearchState {
  globalSearchQuery: string;
  recentSearches: string[];
  searchHistory: {
    query: string;
    timestamp: Date;
    results: number;
  }[];
  setGlobalSearchQuery: (query: string) => void;
  addRecentSearch: (query: string) => void;
  clearRecentSearches: () => void;
  addSearchToHistory: (query: string, results: number) => void;
}

// User preferences interface
interface UserPreferences {
  language: 'en' | 'vi';
  dateFormat: 'US' | 'EU' | 'ISO';
  timezone: string;
  notificationSettings: {
    browser: boolean;
    email: boolean;
    taskUpdates: boolean;
    resourceAssignments: boolean;
  };
  ui: {
    compactMode: boolean;
    showTaskCodes: boolean;
    defaultTaskView: 'list' | 'kanban' | 'calendar';
    itemsPerPage: number;
  };
  setLanguage: (language: 'en' | 'vi') => void;
  setDateFormat: (format: 'US' | 'EU' | 'ISO') => void;
  setTimezone: (timezone: string) => void;
  updateNotificationSettings: (settings: Partial<UserPreferences['notificationSettings']>) => void;
  updateUISettings: (settings: Partial<UserPreferences['ui']>) => void;
}

// Combined app state
type AppState = ThemeState & UIState & TaskState & ResourceState & SearchState & UserPreferences;

// Create the store with middleware
export const useAppStore = create<AppState>()(
  devtools(
    persist(
      immer((set, get) => ({
        // Theme state
        mode: 'system' as ThemeMode,
        setMode: (mode) =>
          set((state) => {
            state.mode = mode;
          }),
        toggleMode: () =>
          set((state) => {
            const currentEffective = get().getEffectiveTheme();
            state.mode = currentEffective === 'light' ? 'dark' : 'light';
          }),
        getEffectiveTheme: () => {
          const { mode } = get();
          if (mode === 'system') {
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
          }
          return mode;
        },

        // UI state
        sidebarCollapsed: false,
        currentView: 'dashboard' as AppView,
        isLoading: false,
        error: null,
        notifications: [],
        setSidebarCollapsed: (collapsed) =>
          set((state) => {
            state.sidebarCollapsed = collapsed;
          }),
        toggleSidebar: () =>
          set((state) => {
            state.sidebarCollapsed = !state.sidebarCollapsed;
          }),
        setCurrentView: (view) =>
          set((state) => {
            state.currentView = view;
          }),
        setLoading: (loading) =>
          set((state) => {
            state.isLoading = loading;
          }),
        setError: (error) =>
          set((state) => {
            state.error = error;
          }),
        addNotification: (notification) =>
          set((state) => {
            const id = crypto.randomUUID();
            state.notifications.push({ ...notification, id });
          }),
        removeNotification: (id) =>
          set((state) => {
            state.notifications = state.notifications.filter((n) => n.id !== id);
          }),
        clearNotifications: () =>
          set((state) => {
            state.notifications = [];
          }),

        // Task state
        selectedTaskId: null,
        selectedTaskIds: new Set<number>(),
        taskFilters: {},
        setSelectedTaskId: (id) =>
          set((state) => {
            state.selectedTaskId = id;
          }),
        toggleTaskSelection: (id) =>
          set((state) => {
            if (state.selectedTaskIds.has(id)) {
              state.selectedTaskIds.delete(id);
            } else {
              state.selectedTaskIds.add(id);
            }
          }),
        setTaskSelection: (ids) =>
          set((state) => {
            state.selectedTaskIds = new Set(ids);
          }),
        clearTaskSelection: () =>
          set((state) => {
            state.selectedTaskIds.clear();
          }),
        setTaskFilters: (filters) =>
          set((state) => {
            state.taskFilters = filters;
          }),
        updateTaskFilter: (key, value) =>
          set((state) => {
            state.taskFilters[key as keyof typeof state.taskFilters] = value;
          }),

        // Resource state
        selectedResourceIds: new Set<number>(),
        resourceFilters: {},
        toggleResourceSelection: (id) =>
          set((state) => {
            if (state.selectedResourceIds.has(id)) {
              state.selectedResourceIds.delete(id);
            } else {
              state.selectedResourceIds.add(id);
            }
          }),
        setResourceSelection: (ids) =>
          set((state) => {
            state.selectedResourceIds = new Set(ids);
          }),
        clearResourceSelection: () =>
          set((state) => {
            state.selectedResourceIds.clear();
          }),
        setResourceFilters: (filters) =>
          set((state) => {
            state.resourceFilters = filters;
          }),
        updateResourceFilter: (key, value) =>
          set((state) => {
            state.resourceFilters[key as keyof typeof state.resourceFilters] = value;
          }),

        // Search state
        globalSearchQuery: '',
        recentSearches: [],
        searchHistory: [],
        setGlobalSearchQuery: (query) =>
          set((state) => {
            state.globalSearchQuery = query;
          }),
        addRecentSearch: (query) =>
          set((state) => {
            const filtered = state.recentSearches.filter((s) => s !== query);
            state.recentSearches = [query, ...filtered].slice(0, 10);
          }),
        clearRecentSearches: () =>
          set((state) => {
            state.recentSearches = [];
          }),
        addSearchToHistory: (query, results) =>
          set((state) => {
            state.searchHistory.unshift({
              query,
              results,
              timestamp: new Date(),
            });
            // Keep only last 50 searches
            state.searchHistory = state.searchHistory.slice(0, 50);
          }),

        // User preferences
        language: 'en',
        dateFormat: 'US',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        notificationSettings: {
          browser: true,
          email: false,
          taskUpdates: true,
          resourceAssignments: true,
        },
        ui: {
          compactMode: false,
          showTaskCodes: true,
          defaultTaskView: 'list',
          itemsPerPage: 25,
        },
        setLanguage: (language) =>
          set((state) => {
            state.language = language;
          }),
        setDateFormat: (format) =>
          set((state) => {
            state.dateFormat = format;
          }),
        setTimezone: (timezone) =>
          set((state) => {
            state.timezone = timezone;
          }),
        updateNotificationSettings: (settings) =>
          set((state) => {
            Object.assign(state.notificationSettings, settings);
          }),
        updateUISettings: (settings) =>
          set((state) => {
            Object.assign(state.ui, settings);
          }),
      })),
      {
        name: 'ai-work-os-store',
        partialize: (state) => ({
          // Persist only specific state
          mode: state.mode,
          sidebarCollapsed: state.sidebarCollapsed,
          taskFilters: state.taskFilters,
          resourceFilters: state.resourceFilters,
          recentSearches: state.recentSearches,
          language: state.language,
          dateFormat: state.dateFormat,
          timezone: state.timezone,
          ui: state.ui,
        }),
        version: 1,
        migrate: (persistedState: any, version: number) => {
          // Handle state migrations when version changes
          if (version === 0) {
            // Migration from version 0 to 1
            return {
              ...persistedState,
              notificationSettings: {
                browser: true,
                email: false,
                taskUpdates: true,
                resourceAssignments: true,
              },
            };
          }
          return persistedState;
        },
      }
    ),
    {
      name: 'ai-work-os-store',
    }
  )
);

// Selectors for common use cases
export const useTheme = () => useAppStore((state) => ({
  mode: state.mode,
  setMode: state.setMode,
  toggleMode: state.toggleMode,
  getEffectiveTheme: state.getEffectiveTheme,
}));

export const useUI = () => useAppStore((state) => ({
  sidebarCollapsed: state.sidebarCollapsed,
  currentView: state.currentView,
  isLoading: state.isLoading,
  error: state.error,
  notifications: state.notifications,
  setSidebarCollapsed: state.setSidebarCollapsed,
  toggleSidebar: state.toggleSidebar,
  setCurrentView: state.setCurrentView,
  setLoading: state.setLoading,
  setError: state.setError,
  addNotification: state.addNotification,
  removeNotification: state.removeNotification,
  clearNotifications: state.clearNotifications,
}));

export const useTasks = () => useAppStore((state) => ({
  selectedTaskId: state.selectedTaskId,
  selectedTaskIds: state.selectedTaskIds,
  taskFilters: state.taskFilters,
  setSelectedTaskId: state.setSelectedTaskId,
  toggleTaskSelection: state.toggleTaskSelection,
  setTaskSelection: state.setTaskSelection,
  clearTaskSelection: state.clearTaskSelection,
  setTaskFilters: state.setTaskFilters,
  updateTaskFilter: state.updateTaskFilter,
}));

export const useResources = () => useAppStore((state) => ({
  selectedResourceIds: state.selectedResourceIds,
  resourceFilters: state.resourceFilters,
  toggleResourceSelection: state.toggleResourceSelection,
  setResourceSelection: state.setResourceSelection,
  clearResourceSelection: state.clearResourceSelection,
  setResourceFilters: state.setResourceFilters,
  updateResourceFilter: state.updateResourceFilter,
}));

export const useSearch = () => useAppStore((state) => ({
  globalSearchQuery: state.globalSearchQuery,
  recentSearches: state.recentSearches,
  searchHistory: state.searchHistory,
  setGlobalSearchQuery: state.setGlobalSearchQuery,
  addRecentSearch: state.addRecentSearch,
  clearRecentSearches: state.clearRecentSearches,
  addSearchToHistory: state.addSearchToHistory,
}));

export const usePreferences = () => useAppStore((state) => ({
  language: state.language,
  dateFormat: state.dateFormat,
  timezone: state.timezone,
  notificationSettings: state.notificationSettings,
  ui: state.ui,
  setLanguage: state.setLanguage,
  setDateFormat: state.setDateFormat,
  setTimezone: state.setTimezone,
  updateNotificationSettings: state.updateNotificationSettings,
  updateUISettings: state.updateUISettings,
}));

// Action creators for complex operations
export const appActions = {
  // Show notification with auto-dismiss
  showNotification: (
    notification: Omit<Notification, 'id'>,
    duration = 5000
  ) => {
    const { addNotification, removeNotification } = useAppStore.getState();
    const id = crypto.randomUUID();
    const fullNotification = { ...notification, id };
    
    addNotification(fullNotification);
    
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, duration);
    }
    
    return id;
  },

  // Show error notification
  showError: (message: string, title = 'Error') => {
    return appActions.showNotification({
      type: 'error',
      title,
      message,
    });
  },

  // Show success notification
  showSuccess: (message: string, title = 'Success') => {
    return appActions.showNotification({
      type: 'success',
      title,
      message,
    });
  },

  // Initialize app state
  initializeApp: async () => {
    const { setLoading, setError } = useAppStore.getState();
    
    try {
      setLoading(true);
      setError(null);
      
      // Initialize any required app state
      // This could include checking authentication, loading user preferences, etc.
      
      // For now, just complete initialization immediately
      console.log('App initialized successfully');
      
    } catch (error) {
      console.error('App initialization error:', error);
      setError(error instanceof Error ? error.message : 'Failed to initialize app');
    } finally {
      // Always set loading to false
      setLoading(false);
    }
  },

  // Reset app state
  resetApp: () => {
    const store = useAppStore.getState();
    store.clearTaskSelection();
    store.clearResourceSelection();
    store.clearNotifications();
    store.setSelectedTaskId(null);
    store.setError(null);
    store.setGlobalSearchQuery('');
  },
};

export default useAppStore;
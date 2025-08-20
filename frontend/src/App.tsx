import React, { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

// Layout components
import { AppLayout } from '@/components/layout/AppLayout';
import { LoadingScreen } from '@/components/common/LoadingScreen';

// Page components
import { DashboardPage } from '@/pages/DashboardPage';
import { TasksPage } from '@/pages/TasksPage';
import { ResourcesPage } from '@/pages/ResourcesPage';
import { QAPage } from '@/pages/QAPage';
import { IngestPage } from '@/pages/IngestPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

// Hooks and stores
import { useAppStore, useTheme, appActions } from '@/stores/app-store';
import { useSystemStatus } from '@/hooks/useSystemStatus';

// Utilities
import { cn } from '@/utils/cn';

// Theme effect to apply dark/light mode
function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { mode, getEffectiveTheme } = useTheme();

  useEffect(() => {
    const root = window.document.documentElement;
    const effectiveTheme = getEffectiveTheme();
    
    root.classList.remove('light', 'dark');
    root.classList.add(effectiveTheme);
    
    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute(
        'content',
        effectiveTheme === 'dark' ? '#1a1a1a' : '#ffffff'
      );
    }
  }, [mode, getEffectiveTheme]);

  // Listen for system theme changes when in system mode
  useEffect(() => {
    if (mode !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      const root = window.document.documentElement;
      const effectiveTheme = getEffectiveTheme();
      
      root.classList.remove('light', 'dark');
      root.classList.add(effectiveTheme);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [mode, getEffectiveTheme]);

  return <>{children}</>;
}

// Page transition animations
const pageVariants = {
  initial: {
    opacity: 0,
    x: -20,
    scale: 0.98,
  },
  in: {
    opacity: 1,
    x: 0,
    scale: 1,
  },
  out: {
    opacity: 0,
    x: 20,
    scale: 0.98,
  },
};

const pageTransition = {
  type: 'tween',
  ease: 'anticipate',
  duration: 0.3,
};

// Animated page wrapper
function AnimatedPage({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial="initial"
        animate="in"
        exit="out"
        variants={pageVariants}
        transition={pageTransition}
        className="h-full"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

// Main App component
function App() {
  const isLoading = useAppStore((state) => state.isLoading);
  const error = useAppStore((state) => state.error);
  
  // Debug logging
  console.log('App render - isLoading:', isLoading, 'error:', error);
  
  // Initialize app
  useEffect(() => {
    // Temporarily skip initialization to debug loading issue
    const initApp = async () => {
      try {
        await appActions.initializeApp();
      } catch (error) {
        console.error('App initialization failed:', error);
      }
    };
    
    initApp();
  }, []);

  // System status monitoring (with error handling)
  let systemStatus = null;
  let systemError = false;
  
  try {
    const statusQuery = useSystemStatus();
    systemStatus = statusQuery.data;
    systemError = statusQuery.isError;
  } catch (error) {
    console.warn('System status monitoring failed:', error);
    systemError = false; // Don't block app if system status fails
  }

  // Show system-wide error if critical services are down
  useEffect(() => {
    if (systemError || systemStatus?.status === 'down') {
      appActions.showError(
        'System services are currently unavailable. Please try again later.',
        'Service Unavailable'
      );
    }
  }, [systemError, systemStatus]);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip if user is typing in an input
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        event.target instanceof HTMLSelectElement ||
        (event.target as HTMLElement)?.contentEditable === 'true'
      ) {
        return;
      }

      // Global shortcuts
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 'k':
            event.preventDefault();
            // Focus global search (will be implemented)
            document.getElementById('global-search')?.focus();
            break;
          case '/':
            event.preventDefault();
            // Open command palette (future feature)
            break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Show loading screen during initial app load  
  // Temporary bypass for debugging
  const shouldShowLoading = false; // isLoading;
  
  if (shouldShowLoading) {
    return <LoadingScreen />;
  }

  // Show error state if app failed to initialize
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold text-destructive">
            Failed to Load Application
          </h1>
          <p className="text-muted-foreground max-w-md">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Reload Application
          </button>
        </div>
      </div>
    );
  }

  return (
    <ThemeProvider>
      <div className="h-screen bg-background text-foreground overflow-hidden">
        <AppLayout>
          <AnimatedPage>
            <Routes>
              {/* Default redirect to dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              
              {/* Main application routes */}
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/tasks/*" element={<TasksPage />} />
              <Route path="/resources/*" element={<ResourcesPage />} />
              <Route path="/qa" element={<QAPage />} />
              <Route path="/ingest" element={<IngestPage />} />
              <Route path="/settings/*" element={<SettingsPage />} />
              
              {/* 404 page */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </AnimatedPage>
        </AppLayout>
      </div>
    </ThemeProvider>
  );
}

export default App;
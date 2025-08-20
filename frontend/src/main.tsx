import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';

import App from './App';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { PWAInstallPrompt } from '@/components/common/PWAInstallPrompt';
import '@/index.css';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors except 408, 429
        if (error?.status >= 400 && error?.status < 500 && ![408, 429].includes(error?.status)) {
          return false;
        }
        return failureCount < 3;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: false,
    },
  },
});

// Enhanced error handler for React Query
queryClient.setMutationDefaults(['tasks'], {
  mutationFn: async (variables: any) => {
    // This will be overridden by specific mutations
    throw new Error('Mutation function not implemented');
  },
  onError: (error: any) => {
    console.error('Mutation error:', error);
    // Could integrate with error reporting service here
  },
});

// Service Worker Registration for PWA
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration);
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

// Performance monitoring
if (import.meta.env.DEV) {
  // Enable React DevTools profiler in development
  window.__REACT_DEVTOOLS_GLOBAL_HOOK__?.settings &&
    (window.__REACT_DEVTOOLS_GLOBAL_HOOK__.settings.appendComponentStack = true);
}

// Initialize app
const initializeApp = async () => {
  // Any async initialization logic can go here
  // e.g., checking authentication, loading critical config, etc.
  
  // For now, we'll just render immediately
  return Promise.resolve();
};

// Root element
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found');
}

const root = ReactDOM.createRoot(rootElement);

// Global error handler
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  // Could integrate with error reporting service here
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  // Could integrate with error reporting service here
});

// Render the app
initializeApp().then(() => {
  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <BrowserRouter>
          <QueryClientProvider client={queryClient}>
            <App />
            
            {/* Global toast notifications */}
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: 'hsl(var(--card))',
                  color: 'hsl(var(--card-foreground))',
                  border: '1px solid hsl(var(--border))',
                },
                success: {
                  iconTheme: {
                    primary: 'hsl(var(--primary))',
                    secondary: 'white',
                  },
                },
                error: {
                  iconTheme: {
                    primary: 'hsl(var(--destructive))',
                    secondary: 'white',
                  },
                },
              }}
            />
            
            {/* PWA Install Prompt */}
            <PWAInstallPrompt />
            
            {/* React Query DevTools in development */}
            {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
          </QueryClientProvider>
        </BrowserRouter>
      </ErrorBoundary>
    </React.StrictMode>
  );
});

// Hot Module Replacement (HMR) for development
if (import.meta.hot) {
  import.meta.hot.accept();
}
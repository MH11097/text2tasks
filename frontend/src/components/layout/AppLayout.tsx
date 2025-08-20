import React from 'react';
import { useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { useUI } from '@/stores/app-store';
import { cn } from '@/utils/cn';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const { sidebarCollapsed } = useUI();
  const location = useLocation();

  // Don't show sidebar on certain pages
  const hideSidebar = location.pathname === '/login' || location.pathname === '/register';

  return (
    <div className="h-screen bg-background flex overflow-hidden">
      {/* Sidebar */}
      {!hideSidebar && (
        <motion.aside
          initial={false}
          animate={{
            width: sidebarCollapsed ? '4rem' : '16rem',
          }}
          transition={{
            duration: 0.3,
            ease: 'easeInOut',
          }}
          className="relative bg-card border-r border-border flex-shrink-0 overflow-hidden"
        >
          <Sidebar />
        </motion.aside>
      )}

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Page content */}
        <main
          className={cn(
            'flex-1 overflow-auto',
            // Add padding based on sidebar state
            !hideSidebar && 'transition-all duration-300'
          )}
        >
          <div className="h-full">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile sidebar overlay */}
      {!hideSidebar && !sidebarCollapsed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 md:hidden"
          onClick={() => {
            const { setSidebarCollapsed } = useUI.getState();
            setSidebarCollapsed(true);
          }}
        />
      )}
    </div>
  );
};
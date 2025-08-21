import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Home,
  CheckSquare,
  FileText,
  MessageCircle,
  PlusCircle,
  BarChart3,
  Settings,
  Zap,
  BookOpen,
  Users,
  Calendar,
  Archive,
} from 'lucide-react';

import { useUI } from '@/stores/app-store';
import { cn } from '@/utils/cn';

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  path: string;
  badge?: string | number;
  description?: string;
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

const navigationSections: NavSection[] = [
  {
    title: 'Main',
    items: [
      {
        id: 'tasks',
        label: 'Tasks',
        icon: CheckSquare,
        path: '/tasks',
        description: 'Task management and creation',
      },
      {
        id: 'documents',
        label: 'Documents',
        icon: FileText,
        path: '/documents',
        description: 'Document library and management',
      },
      {
        id: 'qa',
        label: 'Q&A',
        icon: MessageCircle,
        path: '/qa',
        description: 'AI-powered question answering',
      },
    ],
  },
];

const bottomNavItems: NavItem[] = [
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    path: '/settings',
    description: 'App preferences and configuration',
  },
];

export const Sidebar: React.FC = () => {
  const { sidebarCollapsed } = useUI();
  const location = useLocation();

  const isActiveRoute = (path: string) => {
    if (path === '/tasks') {
      return location.pathname === '/tasks' || location.pathname === '/' || location.pathname === '/dashboard';
    }
    if (path === '/documents') {
      return location.pathname.startsWith('/documents') || location.pathname.startsWith('/resources');
    }
    return location.pathname.startsWith(path);
  };

  const renderNavItem = (item: NavItem, index: number) => {
    const isActive = isActiveRoute(item.path);
    
    return (
      <motion.div
        key={item.id}
        initial={false}
        animate={{
          opacity: 1,
          transition: { delay: index * 0.05 },
        }}
      >
        <NavLink
          to={item.path}
          className={({ isActive: linkActive }) =>
            cn(
              'group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
              'hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
              (isActive || linkActive) && 'bg-primary/10 text-primary',
              !isActive && !linkActive && 'text-muted-foreground hover:text-foreground'
            )
          }
          title={sidebarCollapsed ? item.label : undefined}
        >
          <div className="relative flex-shrink-0">
            <item.icon
              className={cn(
                'h-5 w-5 transition-transform group-hover:scale-110',
                isActive && 'text-primary'
              )}
            />
            {item.badge && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1 bg-destructive text-destructive-foreground text-xs rounded-full h-4 w-4 flex items-center justify-center"
              >
                {typeof item.badge === 'number' && item.badge > 9 ? '9+' : item.badge}
              </motion.div>
            )}
          </div>
          
          {!sidebarCollapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className="flex-1 min-w-0"
            >
              <div className="font-medium">{item.label}</div>
              {item.description && (
                <div className="text-xs text-muted-foreground truncate">
                  {item.description}
                </div>
              )}
            </motion.div>
          )}
          
          {isActive && (
            <motion.div
              layoutId="sidebar-active-indicator"
              className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r-full"
              transition={{ type: 'spring', damping: 25, stiffness: 400 }}
            />
          )}
        </NavLink>
      </motion.div>
    );
  };

  const renderSection = (section: NavSection, sectionIndex: number) => (
    <div key={`section-${sectionIndex}`} className="space-y-1">
      {section.title && !sidebarCollapsed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: sectionIndex * 0.1 }}
          className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider"
        >
          {section.title}
        </motion.div>
      )}
      <div className="space-y-1">
        {section.items.map((item, index) => renderNavItem(item, index))}
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-card border-r border-border">
      {/* Logo section */}
      <div className="p-4 border-b border-border">
        <motion.div
          className="flex items-center gap-3"
          animate={{
            justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
          }}
          transition={{ duration: 0.3 }}
        >
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <Zap className="h-5 w-5 text-primary-foreground" />
          </div>
          {!sidebarCollapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
            >
              <h1 className="font-bold text-lg text-foreground">AI Work OS</h1>
              <p className="text-xs text-muted-foreground">Task Management</p>
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Navigation sections */}
      <div className="flex-1 overflow-y-auto py-4 space-y-6">
        <div className="px-2 space-y-6">
          {navigationSections.map((section, index) => renderSection(section, index))}
        </div>
      </div>

      {/* Bottom navigation */}
      <div className="p-2 border-t border-border">
        <div className="space-y-1">
          {bottomNavItems.map((item, index) => renderNavItem(item, index))}
        </div>
      </div>

      {/* Collapse indicator */}
      {!sidebarCollapsed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="px-4 py-2 border-t border-border"
        >
          <div className="text-xs text-muted-foreground text-center">
            Press <kbd className="px-1 py-0.5 bg-muted border border-border rounded text-xs">⌘ B</kbd> to toggle
          </div>
        </motion.div>
      )}
    </div>
  );
};
import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  FileText,
  MessageSquare,
  Plus,
  ArrowRight,
} from 'lucide-react';

import { api } from '@/services/api';
import { useUI } from '@/stores/app-store';
import { formatRelativeTime, formatNumber } from '@/utils/format';
import { cn } from '@/utils/cn';

interface StatCard {
  title: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

export const DashboardPage: React.FC = () => {
  const { setCurrentView } = useUI();

  // Fetch dashboard data
  const { data: systemStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => api.status.getStatus(),
  });

  const { data: resourceStats, isLoading: statsLoading } = useQuery({
    queryKey: ['resource-stats'],
    queryFn: () => api.status.getResourceStats(),
  });

  React.useEffect(() => {
    setCurrentView('dashboard');
  }, [setCurrentView]);

  const isLoading = statusLoading || statsLoading;

  // Calculate stats for cards
  const statCards: StatCard[] = [
    {
      title: 'Total Tasks',
      value: resourceStats?.task_hierarchy.total_tasks || 0,
      change: '+12%',
      trend: 'up',
      icon: CheckCircle,
      color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/20',
    },
    {
      title: 'In Progress',
      value: systemStatus?.tasks_summary.in_progress || 0,
      change: '+5%',
      trend: 'up',
      icon: Clock,
      color: 'text-orange-600 bg-orange-100 dark:bg-orange-900/20',
    },
    {
      title: 'Completed',
      value: systemStatus?.tasks_summary.done || 0,
      change: '+23%',
      trend: 'up',
      icon: CheckCircle,
      color: 'text-green-600 bg-green-100 dark:bg-green-900/20',
    },
    {
      title: 'Resources',
      value: resourceStats?.resource_assignment.total_resources || 0,
      change: '+8%',
      trend: 'up',
      icon: FileText,
      color: 'text-purple-600 bg-purple-100 dark:bg-purple-900/20',
    },
  ];

  const quickActions = [
    {
      title: 'Create Task',
      description: 'Add a new task to your hierarchy',
      icon: Plus,
      action: () => {},
      color: 'bg-primary text-primary-foreground',
    },
    {
      title: 'Add Document',
      description: 'Import and extract tasks from documents',
      icon: FileText,
      action: () => {},
      color: 'bg-secondary text-secondary-foreground',
    },
    {
      title: 'Ask Question',
      description: 'Get AI-powered answers from your data',
      icon: MessageSquare,
      action: () => {},
      color: 'bg-accent text-accent-foreground',
    },
  ];

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-card border border-border rounded-lg p-6">
              <div className="animate-pulse space-y-4">
                <div className="w-8 h-8 bg-muted rounded-lg" />
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-8 bg-muted rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's what's happening with your work.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            Last updated {formatRelativeTime(new Date())}
          </span>
          <div className={cn(
            'w-2 h-2 rounded-full',
            systemStatus?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
          )} />
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {statCards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + index * 0.05 }}
            className="bg-card border border-border rounded-lg p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className={cn('p-2 rounded-lg', card.color)}>
                <card.icon className="h-5 w-5" />
              </div>
              {card.change && (
                <div className={cn(
                  'flex items-center gap-1 text-sm',
                  card.trend === 'up' ? 'text-green-600' : card.trend === 'down' ? 'text-red-600' : 'text-muted-foreground'
                )}>
                  <TrendingUp className="h-3 w-3" />
                  {card.change}
                </div>
              )}
            </div>
            
            <div className="mt-4">
              <div className="text-2xl font-bold text-foreground">
                {formatNumber(Number(card.value))}
              </div>
              <div className="text-sm text-muted-foreground">{card.title}</div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="space-y-4"
      >
        <h2 className="text-xl font-semibold text-foreground">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action, index) => (
            <motion.button
              key={action.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.05 }}
              onClick={action.action}
              className={cn(
                'p-6 rounded-lg text-left transition-all hover:scale-105 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                action.color
              )}
            >
              <div className="flex items-center justify-between mb-4">
                <action.icon className="h-6 w-6" />
                <ArrowRight className="h-4 w-4 opacity-60" />
              </div>
              <h3 className="font-semibold mb-1">{action.title}</h3>
              <p className="text-sm opacity-80">{action.description}</p>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* Recent Tasks */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">Recent Tasks</h3>
            <button className="text-sm text-primary hover:underline">
              View all
            </button>
          </div>
          
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center gap-3 p-3 hover:bg-muted/50 rounded-lg transition-colors">
                <div className="w-2 h-2 bg-primary rounded-full" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-foreground truncate">
                    Sample Task {i + 1}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Updated {formatRelativeTime(new Date(Date.now() - i * 3600000))}
                  </div>
                </div>
                <div className="text-xs bg-muted px-2 py-1 rounded">
                  In Progress
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Health */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">System Health</h3>
            <div className={cn(
              'w-2 h-2 rounded-full',
              systemStatus?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
            )} />
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-foreground">Database</span>
              <span className={cn(
                'text-xs px-2 py-1 rounded',
                systemStatus?.database === 'connected' 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                  : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
              )}>
                {systemStatus?.database}
              </span>
            </div>
            
            {systemStatus?.recent_activity && (
              <div className="pt-3 border-t border-border">
                <div className="text-sm text-muted-foreground">Recent Activity</div>
                <div className="text-foreground mt-1">{systemStatus.recent_activity}</div>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
};
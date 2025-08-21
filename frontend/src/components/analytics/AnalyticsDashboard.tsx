import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  CheckCircle,
  AlertCircle,
  Target,
} from 'lucide-react';

interface Task {
  id: number;
  title: string;
  status: 'new' | 'in_progress' | 'blocked' | 'done';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  owner?: string;
  created_at: string;
  updated_at: string;
  due_date?: string;
}

interface AnalyticsDashboardProps {
  tasks: Task[];
  className?: string;
}

interface StatCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
  };
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, icon: Icon, color }) => {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="bg-card border border-border rounded-lg p-6 hover:shadow-lg transition-all duration-200"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground mb-1">{title}</p>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {change && (
            <div className="flex items-center gap-1 mt-2">
              {change.type === 'increase' ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span
                className={`text-sm font-medium ${
                  change.type === 'increase' ? 'text-green-500' : 'text-red-500'
                }`}
              >
                {change.value > 0 ? '+' : ''}{change.value}%
              </span>
            </div>
          )}
        </div>
        <div className={`w-12 h-12 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </motion.div>
  );
};

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ 
  tasks, 
  className = '' 
}) => {
  const analytics = useMemo(() => {
    // Status distribution
    const statusCounts = tasks.reduce((acc, task) => {
      acc[task.status] = (acc[task.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Priority distribution
    const priorityCounts = tasks.reduce((acc, task) => {
      const priority = task.priority || 'medium';
      acc[priority] = (acc[priority] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Tasks by week (last 4 weeks)
    const now = new Date();
    const weeklyData = [];
    for (let i = 3; i >= 0; i--) {
      const weekStart = new Date(now);
      weekStart.setDate(now.getDate() - (i * 7));
      weekStart.setHours(0, 0, 0, 0);
      
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekStart.getDate() + 7);
      
      const weekTasks = tasks.filter(task => {
        const taskDate = new Date(task.created_at);
        return taskDate >= weekStart && taskDate < weekEnd;
      });
      
      weeklyData.push({
        week: `Week ${4 - i}`,
        created: weekTasks.length,
        completed: weekTasks.filter(t => t.status === 'done').length,
      });
    }

    // Completion rate
    const completedTasks = statusCounts.done || 0;
    const totalTasks = tasks.length;
    const completionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

    // Overdue tasks
    const overdueTasks = tasks.filter(task => {
      if (!task.due_date || task.status === 'done') return false;
      return new Date(task.due_date) < now;
    }).length;

    return {
      statusCounts,
      priorityCounts,
      weeklyData,
      completionRate,
      overdueTasks,
      totalTasks,
      completedTasks,
    };
  }, [tasks]);

  // Chart data
  const statusChartData = [
    { name: 'New', value: analytics.statusCounts.new || 0, color: '#6B7280' },
    { name: 'In Progress', value: analytics.statusCounts.in_progress || 0, color: '#3B82F6' },
    { name: 'Blocked', value: analytics.statusCounts.blocked || 0, color: '#EF4444' },
    { name: 'Done', value: analytics.statusCounts.done || 0, color: '#10B981' },
  ];

  const priorityChartData = [
    { name: 'Low', value: analytics.priorityCounts.low || 0, fill: '#6B7280' },
    { name: 'Medium', value: analytics.priorityCounts.medium || 0, fill: '#F59E0B' },
    { name: 'High', value: analytics.priorityCounts.high || 0, fill: '#F97316' },
    { name: 'Urgent', value: analytics.priorityCounts.urgent || 0, fill: '#EF4444' },
  ];

  return (
    <div className={className}>
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Tasks"
          value={analytics.totalTasks}
          change={{ value: 12, type: 'increase' }}
          icon={Target}
          color="bg-blue-500"
        />
        <StatCard
          title="Completed"
          value={analytics.completedTasks}
          change={{ value: 8, type: 'increase' }}
          icon={CheckCircle}
          color="bg-green-500"
        />
        <StatCard
          title="Completion Rate"
          value={`${analytics.completionRate}%`}
          change={{ value: 5, type: 'increase' }}
          icon={TrendingUp}
          color="bg-purple-500"
        />
        <StatCard
          title="Overdue"
          value={analytics.overdueTasks}
          change={analytics.overdueTasks > 0 ? { value: -15, type: 'decrease' } : undefined}
          icon={AlertCircle}
          color="bg-red-500"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Status Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-card border border-border rounded-lg p-6"
        >
          <h3 className="text-lg font-semibold text-foreground mb-4">Task Status Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={statusChartData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
              >
                {statusChartData.map((entry, index) => (
                  <Cell key={`status-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Priority Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-card border border-border rounded-lg p-6"
        >
          <h3 className="text-lg font-semibold text-foreground mb-4">Priority Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={priorityChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis dataKey="name" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))', 
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px'
                }} 
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Weekly Progress */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-card border border-border rounded-lg p-6"
      >
        <h3 className="text-lg font-semibold text-foreground mb-4">Weekly Progress</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={analytics.weeklyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
            <XAxis dataKey="week" stroke="#6B7280" />
            <YAxis stroke="#6B7280" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'hsl(var(--card))', 
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px'
              }} 
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="created" 
              stroke="#3B82F6" 
              strokeWidth={3}
              dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
              name="Created"
            />
            <Line 
              type="monotone" 
              dataKey="completed" 
              stroke="#10B981" 
              strokeWidth={3}
              dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
              name="Completed"
            />
          </LineChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
};
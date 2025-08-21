import React, { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitBranch,
  ArrowRight,
  Plus,
  X,
  Link,
  Unlink,
  Search,
  Filter,
  Clock,
  CheckCircle,
  AlertCircle,
  Play,
  Target,
  Network,
  Zap,
  Settings,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface Task {
  id: number;
  title: string;
  status: 'new' | 'in_progress' | 'blocked' | 'done';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  owner?: string;
  created_at: string;
  dependencies?: number[]; // Task IDs this task depends on
  blockedBy?: number[]; // Task IDs that block this task
  blocks?: number[]; // Task IDs this task blocks
}

interface TaskRelationshipsProps {
  tasks: Task[];
  onCreateDependency?: (taskId: number, dependsOnId: number) => void;
  onRemoveDependency?: (taskId: number, dependsOnId: number) => void;
  className?: string;
}

interface DependencyChain {
  task: Task;
  dependencies: Task[];
  blockers: Task[];
  dependents: Task[];
  criticalPath: boolean;
  depth: number;
}

const statusIcons = {
  new: Clock,
  in_progress: Play,
  blocked: AlertCircle,
  done: CheckCircle,
};

const statusColors = {
  new: 'text-gray-500 bg-gray-100 dark:bg-gray-800',
  in_progress: 'text-blue-500 bg-blue-100 dark:bg-blue-900',
  blocked: 'text-red-500 bg-red-100 dark:bg-red-900',
  done: 'text-green-500 bg-green-100 dark:bg-green-900',
};

export const TaskRelationships: React.FC<TaskRelationshipsProps> = ({
  tasks,
  onCreateDependency,
  onRemoveDependency,
  className = '',
}) => {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'graph'>('list');
  const [showAddDependency, setShowAddDependency] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Mock dependency data - in real app, this would come from the tasks
  const tasksWithDependencies: Task[] = useMemo(() => {
    return tasks.map(task => ({
      ...task,
      dependencies: task.id === 1 ? [2] : task.id === 3 ? [1, 2] : [],
      blocks: task.id === 2 ? [1, 3] : task.id === 1 ? [4] : [],
      blockedBy: task.id === 4 ? [1] : [],
    }));
  }, [tasks]);

  // Build dependency chains and critical path
  const dependencyAnalysis = useMemo((): DependencyChain[] => {
    const taskMap = new Map(tasksWithDependencies.map(t => [t.id, t]));
    const chains: DependencyChain[] = [];

    tasksWithDependencies.forEach(task => {
      const dependencies = (task.dependencies || []).map(id => taskMap.get(id)!).filter(Boolean);
      const blockers = (task.blockedBy || []).map(id => taskMap.get(id)!).filter(Boolean);
      const dependents = tasksWithDependencies.filter(t => t.dependencies?.includes(task.id));

      // Calculate depth in dependency chain
      const calculateDepth = (taskId: number, visited = new Set<number>()): number => {
        if (visited.has(taskId)) return 0; // Circular dependency guard
        visited.add(taskId);
        
        const currentTask = taskMap.get(taskId);
        if (!currentTask?.dependencies?.length) return 0;
        
        return 1 + Math.max(...currentTask.dependencies.map(id => calculateDepth(id, new Set(visited))));
      };

      const depth = calculateDepth(task.id);
      
      // Determine if part of critical path (simplified logic)
      const criticalPath = dependencies.some(dep => dep.status !== 'done') || 
                          blockers.length > 0 ||
                          (task.status === 'blocked' && task.priority === 'high');

      chains.push({
        task,
        dependencies,
        blockers,
        dependents,
        criticalPath,
        depth,
      });
    });

    return chains.sort((a, b) => b.depth - a.depth);
  }, [tasksWithDependencies]);

  // Filter chains based on search and status
  const filteredChains = useMemo(() => {
    let filtered = dependencyAnalysis;

    if (searchQuery) {
      filtered = filtered.filter(chain =>
        chain.task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        chain.dependencies.some(dep => 
          dep.title.toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(chain => chain.task.status === filterStatus);
    }

    return filtered;
  }, [dependencyAnalysis, searchQuery, filterStatus]);

  const handleAddDependency = useCallback((taskId: number, dependsOnId: number) => {
    onCreateDependency?.(taskId, dependsOnId);
    setShowAddDependency(false);
  }, [onCreateDependency]);

  const handleRemoveDependency = useCallback((taskId: number, dependsOnId: number) => {
    onRemoveDependency?.(taskId, dependsOnId);
  }, [onRemoveDependency]);

  // Get critical path tasks
  const criticalPathTasks = dependencyAnalysis.filter(chain => chain.criticalPath);
  const blockedTasks = dependencyAnalysis.filter(chain => chain.task.status === 'blocked' || chain.blockers.length > 0);

  return (
    <div className={className}>
      <div className="bg-card border border-border rounded-lg p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-lg flex items-center justify-center">
              <Network className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">Task Relationships</h3>
              <p className="text-sm text-muted-foreground">
                Dependencies, blockers, and critical path analysis
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex border border-border rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'px-3 py-1 rounded text-sm transition-colors',
                  viewMode === 'list' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'hover:bg-muted'
                )}
              >
                List View
              </button>
              <button
                onClick={() => setViewMode('graph')}
                className={cn(
                  'px-3 py-1 rounded text-sm transition-colors',
                  viewMode === 'graph' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'hover:bg-muted'
                )}
              >
                Graph View
              </button>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-background border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center">
                <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Critical Path</p>
                <p className="text-xl font-bold text-foreground">{criticalPathTasks.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-background border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center">
                <X className="h-4 w-4 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Blocked Tasks</p>
                <p className="text-xl font-bold text-foreground">{blockedTasks.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-background border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <GitBranch className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Dependencies</p>
                <p className="text-xl font-bold text-foreground">
                  {dependencyAnalysis.reduce((acc, chain) => acc + chain.dependencies.length, 0)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search tasks and dependencies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All Status</option>
            <option value="new">New</option>
            <option value="in_progress">In Progress</option>
            <option value="blocked">Blocked</option>
            <option value="done">Done</option>
          </select>
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          {viewMode === 'list' && (
            <motion.div
              key="list"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              {filteredChains.length === 0 ? (
                <div className="text-center py-8">
                  <GitBranch className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground">No task dependencies found</p>
                  <p className="text-sm text-muted-foreground/75">
                    Tasks with dependencies will appear here for relationship analysis
                  </p>
                </div>
              ) : (
                filteredChains.map((chain) => {
                  const StatusIcon = statusIcons[chain.task.status];
                  
                  return (
                    <motion.div
                      key={chain.task.id}
                      layout
                      className={cn(
                        'border rounded-lg p-4 transition-all cursor-pointer',
                        chain.criticalPath 
                          ? 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-950/30'
                          : 'border-border bg-background hover:border-primary/50'
                      )}
                      onClick={() => setSelectedTask(
                        selectedTask?.id === chain.task.id ? null : chain.task
                      )}
                    >
                      {/* Task Header */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            'w-8 h-8 rounded-lg flex items-center justify-center',
                            statusColors[chain.task.status]
                          )}>
                            <StatusIcon className="h-4 w-4" />
                          </div>
                          <div>
                            <h4 className="font-medium text-foreground">{chain.task.title}</h4>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <span>Depth: {chain.depth}</span>
                              {chain.criticalPath && (
                                <span className="px-2 py-0.5 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 rounded text-xs font-medium">
                                  Critical Path
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          {chain.dependencies.length > 0 && (
                            <span className="text-sm text-muted-foreground">
                              {chain.dependencies.length} dependencies
                            </span>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowAddDependency(true);
                              setSelectedTask(chain.task);
                            }}
                            className="p-1 rounded hover:bg-muted transition-colors"
                            title="Add dependency"
                          >
                            <Plus className="h-4 w-4" />
                          </button>
                        </div>
                      </div>

                      {/* Dependencies */}
                      {chain.dependencies.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-muted-foreground mb-2">Dependencies:</p>
                          <div className="flex flex-wrap gap-2">
                            {chain.dependencies.map((dep) => {
                              const DepStatusIcon = statusIcons[dep.status];
                              return (
                                <div
                                  key={dep.id}
                                  className="flex items-center gap-2 px-3 py-1 bg-muted rounded-full text-sm"
                                >
                                  <DepStatusIcon className={cn('h-3 w-3', statusColors[dep.status].split(' ')[0])} />
                                  <span>{dep.title}</span>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleRemoveDependency(chain.task.id, dep.id);
                                    }}
                                    className="p-0.5 rounded hover:bg-background transition-colors"
                                    title="Remove dependency"
                                  >
                                    <X className="h-3 w-3" />
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Blockers */}
                      {chain.blockers.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-red-600 dark:text-red-400 mb-2">Blocked by:</p>
                          <div className="flex flex-wrap gap-2">
                            {chain.blockers.map((blocker) => {
                              const BlockerStatusIcon = statusIcons[blocker.status];
                              return (
                                <div
                                  key={blocker.id}
                                  className="flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200 rounded-full text-sm"
                                >
                                  <BlockerStatusIcon className="h-3 w-3" />
                                  <span>{blocker.title}</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Expanded Details */}
                      {selectedTask?.id === chain.task.id && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="border-t border-border pt-3 mt-3"
                        >
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <h5 className="font-medium text-foreground mb-2">This task blocks:</h5>
                              {chain.dependents.length > 0 ? (
                                <div className="space-y-1">
                                  {chain.dependents.map((dependent) => (
                                    <div key={dependent.id} className="text-sm text-muted-foreground">
                                      • {dependent.title}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-muted-foreground">No dependent tasks</p>
                              )}
                            </div>
                            <div>
                              <h5 className="font-medium text-foreground mb-2">Relationship Impact:</h5>
                              <div className="space-y-1 text-sm text-muted-foreground">
                                {chain.criticalPath && (
                                  <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                                    <Zap className="h-3 w-3" />
                                    <span>On critical path - delays affect project timeline</span>
                                  </div>
                                )}
                                <div className="flex items-center gap-2">
                                  <Target className="h-3 w-3" />
                                  <span>Dependency depth: {chain.depth}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <GitBranch className="h-3 w-3" />
                                  <span>{chain.dependents.length} tasks depend on this</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </motion.div>
                  );
                })
              )}
            </motion.div>
          )}

          {viewMode === 'graph' && (
            <motion.div
              key="graph"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-12"
            >
              <Network className="h-16 w-16 text-muted-foreground/50 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-foreground mb-2">Dependency Graph View</h4>
              <p className="text-muted-foreground mb-4">
                Interactive graph visualization coming soon
              </p>
              <p className="text-sm text-muted-foreground">
                This will show tasks as nodes connected by dependency relationships,
                with critical path highlighting and interactive exploration.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Add Dependency Modal */}
      {showAddDependency && selectedTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Add Dependency</h3>
              <button
                onClick={() => setShowAddDependency(false)}
                className="p-1 rounded hover:bg-muted transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Select which task <strong>{selectedTask.title}</strong> depends on:
            </p>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {tasks
                .filter(task => task.id !== selectedTask.id)
                .map((task) => {
                  const StatusIcon = statusIcons[task.status];
                  return (
                    <button
                      key={task.id}
                      onClick={() => handleAddDependency(selectedTask.id, task.id)}
                      className="w-full flex items-center gap-3 p-3 text-left border border-border rounded-lg hover:border-primary/50 transition-colors"
                    >
                      <div className={cn(
                        'w-6 h-6 rounded flex items-center justify-center',
                        statusColors[task.status]
                      )}>
                        <StatusIcon className="h-3 w-3" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{task.title}</p>
                        <p className="text-sm text-muted-foreground capitalize">{task.status}</p>
                      </div>
                    </button>
                  );
                })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
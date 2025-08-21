import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface TaskCounts {
  new: number;
  in_progress: number;
  blocked: number;
  done: number;
}

interface StatusResponse {
  summary: string;
  counts: TaskCounts;
}

interface ResourceStats {
  resource_assignment: {
    total_resources: number;
    resources_by_status: {
      assigned: number;
      unassigned: number;
      archived: number;
    };
  };
  task_hierarchy: {
    total_tasks: number;
    root_tasks: number;
    max_hierarchy_depth: number;
  };
}

interface Task {
  id: string;
  title: string;
  status: string;
  due_date?: string;
  owner?: string;
  source_doc_id: string;
}

export const ResourcesPage: React.FC = () => {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [resourceStats, setResourceStats] = useState<ResourceStats | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch all data in parallel
      const [statusRes, resourceRes, tasksRes] = await Promise.all([
        fetch('/api/v1/status'),
        fetch('/api/v1/resources/stats'),
        fetch('/api/v1/tasks')
      ]);

      if (!statusRes.ok || !resourceRes.ok || !tasksRes.ok) {
        throw new Error('Failed to fetch data');
      }

      const statusData = await statusRes.json();
      const resourceData = await resourceRes.json();
      const tasksData = await tasksRes.json();

      setStatus(statusData);
      setResourceStats(resourceData);
      setTasks(tasksData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredTasks = selectedStatus === 'all' 
    ? tasks 
    : tasks.filter(task => task.status === selectedStatus);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'blocked': return 'bg-red-100 text-red-800 border-red-200';
      case 'done': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 max-w-6xl mx-auto"
      >
        <h1 className="text-3xl font-bold text-foreground mb-6">Resources</h1>
        <div className="bg-card border border-border rounded-lg p-8 text-center">
          <p className="text-muted-foreground">Loading resources...</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 max-w-6xl mx-auto"
    >
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-foreground">Resources</h1>
        <button
          onClick={fetchData}
          className="bg-primary text-primary-foreground py-2 px-4 rounded-md hover:bg-primary/90"
        >
          Refresh
        </button>
      </div>
      
      {error && (
        <div className="bg-destructive/10 border border-destructive rounded-lg p-4 mb-6">
          <p className="text-destructive font-medium">Error:</p>
          <p className="text-destructive">{error}</p>
        </div>
      )}

      <div className="grid gap-6">
        {/* Status Overview */}
        {status && (
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">System Status</h2>
            <div className="bg-background p-4 rounded border mb-4">
              <p className="text-foreground">{status.summary}</p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-blue-50 border border-blue-200 rounded">
                <div className="text-2xl font-bold text-blue-600">{status.counts.new}</div>
                <div className="text-sm text-blue-600">New</div>
              </div>
              <div className="text-center p-3 bg-yellow-50 border border-yellow-200 rounded">
                <div className="text-2xl font-bold text-yellow-600">{status.counts.in_progress}</div>
                <div className="text-sm text-yellow-600">In Progress</div>
              </div>
              <div className="text-center p-3 bg-red-50 border border-red-200 rounded">
                <div className="text-2xl font-bold text-red-600">{status.counts.blocked}</div>
                <div className="text-sm text-red-600">Blocked</div>
              </div>
              <div className="text-center p-3 bg-green-50 border border-green-200 rounded">
                <div className="text-2xl font-bold text-green-600">{status.counts.done}</div>
                <div className="text-sm text-green-600">Done</div>
              </div>
            </div>
          </div>
        )}

        {/* Resource Statistics */}
        {resourceStats && (
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Resource Statistics</h2>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-foreground mb-3">Resource Assignment</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-background rounded">
                    <span className="text-foreground">Total Resources</span>
                    <span className="font-semibold">{resourceStats.resource_assignment.total_resources}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-background rounded">
                    <span className="text-foreground">Assigned</span>
                    <span className="font-semibold text-green-600">{resourceStats.resource_assignment.resources_by_status.assigned}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-background rounded">
                    <span className="text-foreground">Unassigned</span>
                    <span className="font-semibold text-yellow-600">{resourceStats.resource_assignment.resources_by_status.unassigned}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-background rounded">
                    <span className="text-foreground">Archived</span>
                    <span className="font-semibold text-gray-600">{resourceStats.resource_assignment.resources_by_status.archived}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-foreground mb-3">Task Hierarchy</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-background rounded">
                    <span className="text-foreground">Total Tasks</span>
                    <span className="font-semibold">{resourceStats.task_hierarchy.total_tasks}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-background rounded">
                    <span className="text-foreground">Root Tasks</span>
                    <span className="font-semibold">{resourceStats.task_hierarchy.root_tasks}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-background rounded">
                    <span className="text-foreground">Max Depth</span>
                    <span className="font-semibold">{resourceStats.task_hierarchy.max_hierarchy_depth}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tasks List */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-foreground">Tasks ({filteredTasks.length})</h2>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="p-2 bg-background border border-border rounded-md text-foreground"
            >
              <option value="all">All Tasks</option>
              <option value="new">New</option>
              <option value="in_progress">In Progress</option>
              <option value="blocked">Blocked</option>
              <option value="done">Done</option>
            </select>
          </div>
          
          {filteredTasks.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No tasks found.</p>
          ) : (
            <div className="space-y-3">
              {filteredTasks.map((task) => (
                <div key={task.id} className="border border-border rounded-lg p-4 hover:bg-background/50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium text-foreground mb-1">{task.title}</h3>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>ID: {task.id}</span>
                        <span>Source: Doc #{task.source_doc_id}</span>
                        {task.owner && <span>Owner: {task.owner}</span>}
                        {task.due_date && <span>Due: {task.due_date}</span>}
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded border ${getStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
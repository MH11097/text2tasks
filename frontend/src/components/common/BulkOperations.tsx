import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckSquare,
  Square,
  Trash2,
  Edit3,
  Copy,
  Tag,
  User,
  Calendar,
  MoreHorizontal,
  X,
  Check,
  AlertCircle,
  Download,
  Archive,
  Zap,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface Task {
  id: number;
  title: string;
  status: 'new' | 'in_progress' | 'blocked' | 'done';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  owner?: string;
  due_date?: string;
  tags?: string[];
}

interface BulkOperation {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  action: (selectedIds: number[]) => Promise<void> | void;
  requiresConfirmation?: boolean;
  confirmationMessage?: string;
  disabled?: (selectedIds: number[]) => boolean;
}

interface BulkOperationsProps {
  tasks: Task[];
  selectedIds: number[];
  onSelectionChange: (selectedIds: number[]) => void;
  onBulkOperation: (operation: string, selectedIds: number[], data?: any) => Promise<void> | void;
  className?: string;
}

export const BulkOperations: React.FC<BulkOperationsProps> = ({
  tasks,
  selectedIds,
  onSelectionChange,
  onBulkOperation,
  className
}) => {
  const [showConfirmation, setShowConfirmation] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);

  const selectedTasks = tasks.filter(task => selectedIds.includes(task.id));
  const isAllSelected = tasks.length > 0 && selectedIds.length === tasks.length;
  const isPartiallySelected = selectedIds.length > 0 && selectedIds.length < tasks.length;

  const bulkOperations: BulkOperation[] = [
    {
      id: 'status-new',
      label: 'Mark as New',
      icon: Square,
      color: 'text-gray-500',
      action: (ids) => onBulkOperation('status', ids, { status: 'new' })
    },
    {
      id: 'status-in_progress',
      label: 'Mark as In Progress',
      icon: CheckSquare,
      color: 'text-blue-500',
      action: (ids) => onBulkOperation('status', ids, { status: 'in_progress' })
    },
    {
      id: 'status-done',
      label: 'Mark as Done',
      icon: Check,
      color: 'text-green-500',
      action: (ids) => onBulkOperation('status', ids, { status: 'done' })
    },
    {
      id: 'status-blocked',
      label: 'Mark as Blocked',
      icon: AlertCircle,
      color: 'text-red-500',
      action: (ids) => onBulkOperation('status', ids, { status: 'blocked' })
    },
    {
      id: 'priority-low',
      label: 'Set Low Priority',
      icon: Calendar,
      color: 'text-gray-500',
      action: (ids) => onBulkOperation('priority', ids, { priority: 'low' })
    },
    {
      id: 'priority-medium',
      label: 'Set Medium Priority',
      icon: Calendar,
      color: 'text-yellow-500',
      action: (ids) => onBulkOperation('priority', ids, { priority: 'medium' })
    },
    {
      id: 'priority-high',
      label: 'Set High Priority',
      icon: Calendar,
      color: 'text-orange-500',
      action: (ids) => onBulkOperation('priority', ids, { priority: 'high' })
    },
    {
      id: 'priority-urgent',
      label: 'Set Urgent Priority',
      icon: Calendar,
      color: 'text-red-500',
      action: (ids) => onBulkOperation('priority', ids, { priority: 'urgent' })
    },
    {
      id: 'duplicate',
      label: 'Duplicate Tasks',
      icon: Copy,
      color: 'text-purple-500',
      action: (ids) => onBulkOperation('duplicate', ids)
    },
    {
      id: 'archive',
      label: 'Archive Tasks',
      icon: Archive,
      color: 'text-orange-500',
      action: (ids) => onBulkOperation('archive', ids),
      requiresConfirmation: true,
      confirmationMessage: 'Are you sure you want to archive the selected tasks?'
    },
    {
      id: 'export',
      label: 'Export Tasks',
      icon: Download,
      color: 'text-blue-500',
      action: (ids) => onBulkOperation('export', ids)
    },
    {
      id: 'delete',
      label: 'Delete Tasks',
      icon: Trash2,
      color: 'text-red-500',
      action: (ids) => onBulkOperation('delete', ids),
      requiresConfirmation: true,
      confirmationMessage: 'Are you sure you want to permanently delete the selected tasks?'
    }
  ];

  const handleSelectAll = useCallback(() => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(tasks.map(task => task.id));
    }
  }, [isAllSelected, tasks, onSelectionChange]);

  const handleBulkOperation = useCallback(async (operation: BulkOperation) => {
    if (operation.requiresConfirmation) {
      setShowConfirmation(operation.id);
      return;
    }

    setIsProcessing(true);
    try {
      await operation.action(selectedIds);
    } catch (error) {
      console.error('Bulk operation failed:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [selectedIds]);

  const confirmBulkOperation = useCallback(async (operationId: string) => {
    const operation = bulkOperations.find(op => op.id === operationId);
    if (!operation) return;

    setIsProcessing(true);
    try {
      await operation.action(selectedIds);
      setShowConfirmation(null);
    } catch (error) {
      console.error('Bulk operation failed:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [selectedIds, bulkOperations]);

  const getSelectionSummary = () => {
    if (selectedIds.length === 0) return null;
    
    const statusCounts = selectedTasks.reduce((acc, task) => {
      acc[task.status] = (acc[task.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return (
      <div className="text-xs text-muted-foreground">
        {Object.entries(statusCounts).map(([status, count]) => (
          <span key={status} className="mr-2">
            {count} {status.replace('_', ' ')}
          </span>
        ))}
      </div>
    );
  };

  if (selectedIds.length === 0) return null;

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: -10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        className={cn(
          'sticky top-0 z-10 bg-primary/5 border border-primary/20 rounded-lg p-4 mb-4',
          className
        )}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={handleSelectAll}
              className="flex items-center gap-2 hover:bg-primary/10 px-2 py-1 rounded transition-colors"
            >
              <div className="relative">
                {isAllSelected ? (
                  <CheckSquare className="h-5 w-5 text-primary" />
                ) : isPartiallySelected ? (
                  <div className="h-5 w-5 border-2 border-primary rounded bg-primary/20 flex items-center justify-center">
                    <div className="w-2 h-0.5 bg-primary rounded" />
                  </div>
                ) : (
                  <Square className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
              <span className="text-sm font-medium text-foreground">
                {selectedIds.length} of {tasks.length} selected
              </span>
            </button>
            {getSelectionSummary()}
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <button
                onClick={() => setShowBulkActions(!showBulkActions)}
                disabled={isProcessing}
                className="inline-flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {isProcessing ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
                  />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                Bulk Actions
                <MoreHorizontal className="h-4 w-4" />
              </button>

              <AnimatePresence>
                {showBulkActions && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -10 }}
                    className="absolute right-0 top-12 w-72 bg-popover border border-border rounded-lg shadow-lg z-20"
                  >
                    <div className="p-2 max-h-64 overflow-y-auto">
                      <div className="grid grid-cols-1 gap-1">
                        {bulkOperations.map((operation, index) => {
                          const IconComponent = operation.icon;
                          const isDisabled = operation.disabled?.(selectedIds) || isProcessing;
                          
                          return (
                            <motion.button
                              key={operation.id}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.02 }}
                              onClick={() => handleBulkOperation(operation)}
                              disabled={isDisabled}
                              className={cn(
                                'flex items-center gap-3 w-full px-3 py-2 text-sm text-left rounded-md transition-colors',
                                'hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed',
                                operation.color
                              )}
                            >
                              <IconComponent className="h-4 w-4 flex-shrink-0" />
                              <span className="flex-1">{operation.label}</span>
                            </motion.button>
                          );
                        })}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <button
              onClick={() => onSelectionChange([])}
              className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Confirmation Modal */}
      <AnimatePresence>
        {showConfirmation && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-card border border-border rounded-lg p-6 w-full max-w-md"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground">Confirm Action</h3>
                  <p className="text-sm text-muted-foreground">
                    This action cannot be undone
                  </p>
                </div>
              </div>

              <p className="text-sm text-foreground mb-4">
                {bulkOperations.find(op => op.id === showConfirmation)?.confirmationMessage}
              </p>

              <p className="text-sm text-muted-foreground mb-6">
                <strong>{selectedIds.length}</strong> tasks will be affected.
              </p>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowConfirmation(null)}
                  disabled={isProcessing}
                  className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => confirmBulkOperation(showConfirmation)}
                  disabled={isProcessing}
                  className="px-4 py-2 text-sm bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {isProcessing && (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
                    />
                  )}
                  Confirm
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
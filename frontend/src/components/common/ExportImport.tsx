import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Download,
  Upload,
  FileText,
  Database,
  Check,
  AlertCircle,
  X,
  Calendar,
  Filter,
  Settings,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface Task {
  id: number;
  title: string;
  status: 'new' | 'in_progress' | 'blocked' | 'done';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  owner?: string;
  due_date?: string;
  created_at: string;
  updated_at: string;
  description?: string;
  tags?: string[];
}

interface ExportOptions {
  format: 'csv' | 'json' | 'xlsx';
  includeFields: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  statusFilter?: string[];
  priorityFilter?: string[];
}

interface ImportResult {
  success: number;
  failed: number;
  errors: string[];
}

interface ExportImportProps {
  tasks: Task[];
  onExport: (options: ExportOptions) => Promise<void>;
  onImport: (file: File, options: any) => Promise<ImportResult>;
  className?: string;
}

export const ExportImport: React.FC<ExportImportProps> = ({
  tasks,
  onExport,
  onImport,
  className
}) => {
  const [activeTab, setActiveTab] = useState<'export' | 'import'>('export');
  const [isProcessing, setIsProcessing] = useState(false);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'csv',
    includeFields: ['title', 'status', 'priority', 'owner', 'due_date', 'created_at'],
  });
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const availableFields = [
    { key: 'title', label: 'Title', required: true },
    { key: 'description', label: 'Description', required: false },
    { key: 'status', label: 'Status', required: false },
    { key: 'priority', label: 'Priority', required: false },
    { key: 'owner', label: 'Owner', required: false },
    { key: 'due_date', label: 'Due Date', required: false },
    { key: 'created_at', label: 'Created Date', required: false },
    { key: 'updated_at', label: 'Updated Date', required: false },
    { key: 'tags', label: 'Tags', required: false },
  ];

  const formatOptions = [
    { value: 'csv', label: 'CSV', icon: FileText, description: 'Comma-separated values, best for spreadsheets' },
    { value: 'json', label: 'JSON', icon: Database, description: 'JavaScript object notation, best for developers' },
    { value: 'xlsx', label: 'Excel', icon: FileText, description: 'Excel workbook, best for advanced analysis' },
  ];

  const handleExport = useCallback(async () => {
    setIsProcessing(true);
    try {
      await onExport(exportOptions);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [exportOptions, onExport]);

  const handleImport = useCallback(async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    try {
      const result = await onImport(selectedFile, {});
      setImportResult(result);
      setSelectedFile(null);
    } catch (error) {
      console.error('Import failed:', error);
      setImportResult({
        success: 0,
        failed: 1,
        errors: ['Import failed: ' + (error as Error).message]
      });
    } finally {
      setIsProcessing(false);
    }
  }, [selectedFile, onImport]);

  const handleFieldToggle = (fieldKey: string) => {
    const field = availableFields.find(f => f.key === fieldKey);
    if (field?.required) return; // Can't toggle required fields

    setExportOptions(prev => ({
      ...prev,
      includeFields: prev.includeFields.includes(fieldKey)
        ? prev.includeFields.filter(f => f !== fieldKey)
        : [...prev.includeFields, fieldKey]
    }));
  };

  const filteredTasksCount = tasks.filter(task => {
    if (exportOptions.statusFilter?.length) {
      if (!exportOptions.statusFilter.includes(task.status)) return false;
    }
    if (exportOptions.priorityFilter?.length) {
      if (!task.priority || !exportOptions.priorityFilter.includes(task.priority)) return false;
    }
    if (exportOptions.dateRange) {
      const taskDate = new Date(task.created_at);
      const startDate = new Date(exportOptions.dateRange.start);
      const endDate = new Date(exportOptions.dateRange.end);
      if (taskDate < startDate || taskDate > endDate) return false;
    }
    return true;
  }).length;

  return (
    <div className={cn('bg-card border border-border rounded-lg p-6', className)}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-blue-500 rounded-lg flex items-center justify-center">
          <Download className="h-5 w-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">Export & Import</h3>
          <p className="text-sm text-muted-foreground">
            Export your tasks or import from external sources
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-border">
        <button
          onClick={() => setActiveTab('export')}
          className={cn(
            'pb-3 px-1 border-b-2 transition-colors text-sm font-medium',
            activeTab === 'export'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          )}
        >
          <div className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export Data
          </div>
        </button>
        <button
          onClick={() => setActiveTab('import')}
          className={cn(
            'pb-3 px-1 border-b-2 transition-colors text-sm font-medium',
            activeTab === 'import'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          )}
        >
          <div className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Import Data
          </div>
        </button>
      </div>

      <AnimatePresence mode="wait">
        {activeTab === 'export' && (
          <motion.div
            key="export"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-3">
                Export Format
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {formatOptions.map((format) => {
                  const IconComponent = format.icon;
                  return (
                    <button
                      key={format.value}
                      onClick={() => setExportOptions(prev => ({ ...prev, format: format.value as any }))}
                      className={cn(
                        'p-4 border rounded-lg text-left transition-all hover:border-primary/50',
                        exportOptions.format === format.value
                          ? 'border-primary bg-primary/5'
                          : 'border-border'
                      )}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <IconComponent className="h-5 w-5 text-primary" />
                        <span className="font-medium text-foreground">{format.label}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{format.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Field Selection */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-3">
                Fields to Include
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {availableFields.map((field) => (
                  <label
                    key={field.key}
                    className={cn(
                      'flex items-center gap-2 p-3 border rounded-lg cursor-pointer transition-colors',
                      field.required 
                        ? 'border-primary bg-primary/5 cursor-not-allowed opacity-75'
                        : exportOptions.includeFields.includes(field.key)
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={exportOptions.includeFields.includes(field.key)}
                      onChange={() => handleFieldToggle(field.key)}
                      disabled={field.required}
                      className="w-4 h-4 text-primary rounded focus:ring-primary"
                    />
                    <span className="text-sm text-foreground">{field.label}</span>
                    {field.required && (
                      <span className="text-xs text-red-500">*</span>
                    )}
                  </label>
                ))}
              </div>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Date Range (Optional)
                </label>
                <div className="space-y-2">
                  <input
                    type="date"
                    value={exportOptions.dateRange?.start || ''}
                    onChange={(e) => setExportOptions(prev => ({
                      ...prev,
                      dateRange: {
                        ...prev.dateRange,
                        start: e.target.value,
                        end: prev.dateRange?.end || ''
                      }
                    }))}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                  />
                  <input
                    type="date"
                    value={exportOptions.dateRange?.end || ''}
                    onChange={(e) => setExportOptions(prev => ({
                      ...prev,
                      dateRange: {
                        start: prev.dateRange?.start || '',
                        end: e.target.value
                      }
                    }))}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                  />
                </div>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Status Filter (Optional)
                </label>
                <div className="space-y-2">
                  {['new', 'in_progress', 'blocked', 'done'].map((status) => (
                    <label key={status} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={exportOptions.statusFilter?.includes(status) || false}
                        onChange={(e) => {
                          const current = exportOptions.statusFilter || [];
                          setExportOptions(prev => ({
                            ...prev,
                            statusFilter: e.target.checked
                              ? [...current, status]
                              : current.filter(s => s !== status)
                          }));
                        }}
                        className="w-4 h-4 text-primary rounded"
                      />
                      <span className="text-sm text-foreground capitalize">
                        {status.replace('_', ' ')}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Export Summary */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Export Summary</p>
                  <p className="text-xs text-muted-foreground">
                    {filteredTasksCount} tasks will be exported with {exportOptions.includeFields.length} fields
                  </p>
                </div>
                <button
                  onClick={handleExport}
                  disabled={isProcessing || filteredTasksCount === 0}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {isProcessing ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
                    />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                  Export {exportOptions.format.toUpperCase()}
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'import' && (
          <motion.div
            key="import"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-3">
                Select File to Import
              </label>
              <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <div className="space-y-2">
                  <p className="text-lg font-medium text-foreground">
                    {selectedFile ? selectedFile.name : 'Drop your file here or click to browse'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Supports CSV, JSON, and Excel files up to 10MB
                  </p>
                </div>
                <input
                  type="file"
                  accept=".csv,.json,.xlsx,.xls"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="mt-4"
                />
              </div>
            </div>

            {/* Import Options */}
            {selectedFile && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="p-4 bg-muted/50 rounded-lg"
              >
                <h4 className="font-medium text-foreground mb-2">Import Settings</h4>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked className="w-4 h-4 text-primary rounded" />
                    <span className="text-sm text-foreground">Skip duplicate tasks</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" className="w-4 h-4 text-primary rounded" />
                    <span className="text-sm text-foreground">Update existing tasks</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked className="w-4 h-4 text-primary rounded" />
                    <span className="text-sm text-foreground">Validate data before import</span>
                  </label>
                </div>
              </motion.div>
            )}

            {/* Import Button */}
            {selectedFile && (
              <div className="flex justify-end">
                <button
                  onClick={handleImport}
                  disabled={isProcessing}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {isProcessing ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
                    />
                  ) : (
                    <Upload className="h-4 w-4" />
                  )}
                  Import Tasks
                </button>
              </div>
            )}

            {/* Import Results */}
            {importResult && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  'p-4 rounded-lg border',
                  importResult.failed === 0
                    ? 'bg-green-50 border-green-200 dark:bg-green-900 dark:border-green-700'
                    : 'bg-red-50 border-red-200 dark:bg-red-900 dark:border-red-700'
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  {importResult.failed === 0 ? (
                    <Check className="h-5 w-5 text-green-600" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-600" />
                  )}
                  <h4 className="font-medium">Import Complete</h4>
                </div>
                <p className="text-sm mb-2">
                  Successfully imported: {importResult.success} tasks
                </p>
                {importResult.failed > 0 && (
                  <p className="text-sm text-red-600 mb-2">
                    Failed: {importResult.failed} tasks
                  </p>
                )}
                {importResult.errors.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-medium mb-1">Errors:</p>
                    <ul className="text-sm text-red-600 list-disc list-inside">
                      {importResult.errors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
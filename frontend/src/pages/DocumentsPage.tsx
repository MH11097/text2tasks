import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Plus,
  Search,
  Filter,
  MoreVertical,
  Eye,
  Edit3,
  Trash2,
  Download,
  Upload,
  Calendar,
  User,
  Tag,
  CheckSquare,
  X,
} from 'lucide-react';

import { api } from '@/services/api';
import { useUI } from '@/stores/app-store';
import { cn } from '@/utils/cn';
import { formatRelativeTime, formatFileSize } from '@/utils/format';

interface Document {
  id: number;
  title: string;
  summary?: string;
  content: string;
  source_type: string;
  created_at: string;
  updated_at: string;
  file_size?: number;
  task_count?: number;
  tags?: string[];
}

interface DocumentCardProps {
  document: Document;
  onSelect: (id: number) => void;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
}

const DocumentCard: React.FC<DocumentCardProps> = ({ 
  document, 
  onSelect, 
  onEdit, 
  onDelete 
}) => {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="group relative bg-card border border-border rounded-lg p-4 hover:shadow-lg transition-all duration-200 cursor-pointer"
      onClick={() => onSelect(document.id)}
    >
      {/* Document Icon & Title */}
      <div className="flex items-start gap-3 mb-3">
        <div className="flex-shrink-0 w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
          <FileText className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-foreground truncate group-hover:text-primary transition-colors">
            {document.title}
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            {formatRelativeTime(document.created_at)}
          </p>
        </div>
        
        {/* Menu Button */}
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(!showMenu);
            }}
            className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-muted transition-all"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
          
          {showMenu && (
            <div className="absolute right-0 top-8 w-48 bg-popover border border-border rounded-md shadow-lg z-10">
              <div className="py-1">
                <button
                  onClick={(e) => { e.stopPropagation(); onSelect(document.id); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-muted text-left"
                >
                  <Eye className="h-4 w-4" />
                  View Details
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); onEdit(document.id); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-muted text-left"
                >
                  <Edit3 className="h-4 w-4" />
                  Edit
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); /* TODO: Download */ }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-muted text-left"
                >
                  <Download className="h-4 w-4" />
                  Download
                </button>
                <hr className="my-1" />
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(document.id); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-destructive/10 text-destructive text-left"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Summary */}
      {document.summary && (
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
          {document.summary}
        </p>
      )}

      {/* Tags */}
      {document.tags && document.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {document.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-secondary text-secondary-foreground"
            >
              <Tag className="h-3 w-3 mr-1" />
              {tag}
            </span>
          ))}
          {document.tags.length > 3 && (
            <span className="text-xs text-muted-foreground">
              +{document.tags.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <div className="flex items-center gap-4">
          {document.task_count && (
            <span className="flex items-center gap-1">
              <CheckSquare className="h-4 w-4" />
              {document.task_count} tasks
            </span>
          )}
          {document.file_size && (
            <span>{formatFileSize(document.file_size)}</span>
          )}
        </div>
        <span className="text-xs">{document.source_type}</span>
      </div>
    </motion.div>
  );
};

// Document Form Modal Component
interface DocumentFormModalProps {
  onClose: () => void;
  onSave: (documentData: any) => Promise<void>;
}

const DocumentFormModal: React.FC<DocumentFormModalProps> = ({ onClose, onSave }) => {
  const [uploadMode, setUploadMode] = useState<'text' | 'file'>('text');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [formData, setFormData] = useState({
    text: '',
    summary: '',
    source: 'manual',
    source_type: 'document'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (uploadMode === 'text' && !formData.text.trim()) return;
    if (uploadMode === 'file' && !selectedFile) return;
    
    setIsSubmitting(true);
    try {
      if (uploadMode === 'file' && selectedFile) {
        // Handle file upload
        await api.ingest.uploadDocument(selectedFile, formData.summary, (progress) => {
          setUploadProgress(progress);
        });
      } else {
        // Handle text input
        await onSave(formData);
      }
    } catch (error) {
      console.error('Error saving document:', error);
    } finally {
      setIsSubmitting(false);
      setUploadProgress(0);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // Auto-generate summary from filename
      if (!formData.summary) {
        setFormData(prev => ({ 
          ...prev, 
          summary: `Document uploaded from ${file.name}` 
        }));
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card border border-border rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-semibold mb-4">Add Document</h2>
        
        {/* Upload Mode Toggle */}
        <div className="flex items-center justify-center mb-6 bg-muted rounded-lg p-1">
          <button
            type="button"
            onClick={() => setUploadMode('text')}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-colors',
              uploadMode === 'text' 
                ? 'bg-primary text-primary-foreground' 
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            Text Input
          </button>
          <button
            type="button"
            onClick={() => setUploadMode('file')}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-colors',
              uploadMode === 'file' 
                ? 'bg-primary text-primary-foreground' 
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            File Upload
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {uploadMode === 'text' ? (
            <div>
              <label className="block text-sm font-medium mb-1">Content *</label>
              <textarea
                value={formData.text}
                onChange={(e) => setFormData(prev => ({ ...prev, text: e.target.value }))}
                className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Enter document content..."
                rows={8}
                required
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium mb-1">Choose File *</label>
              <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept=".txt,.pdf,.md,.doc,.docx"
                  className="hidden"
                  id="file-upload"
                />
                <label 
                  htmlFor="file-upload" 
                  className="cursor-pointer flex flex-col items-center gap-2"
                >
                  <Upload className="h-8 w-8 text-muted-foreground" />
                  {selectedFile ? (
                    <div className="text-sm">
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-muted-foreground">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      <p>Click to choose a file or drag and drop</p>
                      <p>Supports: .txt, .pdf, .md, .doc, .docx</p>
                    </div>
                  )}
                </label>
              </div>
              
              {isSubmitting && uploadProgress > 0 && (
                <div className="mt-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span>Uploading...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className="bg-primary h-2 rounded-full transition-all duration-300" 
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium mb-1">Summary</label>
            <textarea
              value={formData.summary}
              onChange={(e) => setFormData(prev => ({ ...prev, summary: e.target.value }))}
              className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter document summary..."
              rows={3}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Source</label>
              <select
                value={formData.source}
                onChange={(e) => setFormData(prev => ({ ...prev, source: e.target.value }))}
                className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="manual">Manual</option>
                <option value="email">Email</option>
                <option value="meeting">Meeting</option>
                <option value="note">Note</option>
                <option value="other">Other</option>
                <option value="chat">Chat</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Source Type</label>
              <select
                value={formData.source_type}
                onChange={(e) => setFormData(prev => ({ ...prev, source_type: e.target.value }))}
                className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="document">Document</option>
                <option value="note">Note</option>
                <option value="reference">Reference</option>
              </select>
            </div>
          </div>
          
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-muted-foreground hover:text-foreground"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={(uploadMode === 'text' && !formData.text.trim()) || (uploadMode === 'file' && !selectedFile) || isSubmitting}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (uploadMode === 'file' ? 'Uploading...' : 'Saving...') : 'Add Document'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Document Detail Panel Component
interface DocumentDetailPanelProps {
  document: Document;
  onClose: () => void;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
  navigate: (path: string) => void;
}

const DocumentDetailPanel: React.FC<DocumentDetailPanelProps> = ({ 
  document, 
  onClose, 
  onEdit, 
  onDelete,
  navigate
}) => {
  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="fixed right-0 top-0 h-full w-96 bg-card border-l border-border shadow-xl z-40 overflow-y-auto"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900">
              <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground line-clamp-2">
                {document.title}
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
                  {document.source_type}
                </span>
                {document.task_count && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400">
                    {document.task_count} tasks
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-6">
          {/* Summary */}
          {document.summary && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Summary</h3>
              <p className="text-sm text-foreground whitespace-pre-wrap">{document.summary}</p>
            </div>
          )}

          {/* Content */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Content</h3>
            <div className="bg-muted/30 rounded-lg p-3 max-h-60 overflow-y-auto">
              <p className="text-sm text-foreground whitespace-pre-wrap">{document.content}</p>
            </div>
          </div>

          {/* Details */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Created</h3>
              <span className="text-sm">{formatRelativeTime(document.created_at)}</span>
            </div>

            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Updated</h3>
              <span className="text-sm">{formatRelativeTime(document.updated_at)}</span>
            </div>

            {document.file_size && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Size</h3>
                <span className="text-sm">{formatFileSize(document.file_size)}</span>
              </div>
            )}

            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Source</h3>
              <span className="text-sm capitalize">{document.source_type}</span>
            </div>
          </div>

          {/* Tags */}
          {document.tags && document.tags.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Tags</h3>
              <div className="flex flex-wrap gap-1">
                {document.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground"
                  >
                    <Tag className="h-3 w-3 mr-1" />
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Linked Tasks */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Linked Tasks</h3>
            {document.task_count && document.task_count > 0 ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 p-2 bg-muted/50 rounded-lg">
                  <CheckSquare className="h-4 w-4 text-green-500" />
                  <span className="text-sm">{document.task_count} tasks linked</span>
                </div>
                <button 
                  onClick={() => navigate('/tasks')}
                  className="text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  View All Tasks →
                </button>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">
                <p>No tasks linked to this document</p>
                <button className="text-primary hover:text-primary/80 transition-colors mt-1">
                  + Link Tasks
                </button>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="pt-4 border-t border-border">
            <div className="flex gap-2">
              <button
                onClick={() => onEdit(document.id)}
                className="flex items-center gap-2 px-3 py-2 bg-muted hover:bg-muted/80 rounded-lg text-sm font-medium transition-colors"
              >
                <Edit3 className="h-4 w-4" />
                Edit
              </button>
              <button
                onClick={() => navigate(`/documents/${document.id}`)}
                className="flex items-center gap-2 px-3 py-2 bg-muted hover:bg-muted/80 rounded-lg text-sm font-medium transition-colors"
              >
                <Eye className="h-4 w-4" />
                View Full
              </button>
              <button
                onClick={() => onDelete(document.id)}
                className="flex items-center gap-2 px-3 py-2 bg-destructive/10 hover:bg-destructive/20 text-destructive rounded-lg text-sm font-medium transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export const DocumentsPage: React.FC = () => {
  const { setCurrentView } = useUI();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  React.useEffect(() => {
    setCurrentView('documents');
  }, [setCurrentView]);

  // Fetch documents
  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents', searchQuery, selectedFilter],
    queryFn: async () => {
      try {
        const response = await api.documents.getDocuments();
        return response.documents || response;
      } catch (error) {
        console.error('Failed to fetch documents:', error);
        // Fallback to mock data for development
        return [
          {
            id: 1,
            title: 'Project Requirements Document',
            summary: 'Comprehensive requirements for the new AI Work OS project including functional and non-functional requirements.',
            content: 'Full project requirements...',
            source_type: 'Document',
            created_at: '2024-12-20T10:00:00Z',
            updated_at: '2024-12-21T15:30:00Z',
            file_size: 2048576,
            task_count: 5,
            tags: ['project', 'requirements', 'ai'],
          },
          {
            id: 2,
            title: 'Meeting Notes - Frontend Discussion',
            summary: 'Notes from the team meeting about frontend architecture and implementation strategy.',
            content: 'Meeting notes content...',
            source_type: 'Notes',
            created_at: '2024-12-19T14:00:00Z',
            updated_at: '2024-12-19T16:00:00Z',
            file_size: 512000,
            task_count: 3,
            tags: ['meeting', 'frontend', 'architecture'],
          },
        ] as Document[];
      }
    },
  });

  // Filter documents based on search and filter
  const filteredDocuments = useMemo(() => {
    let filtered = documents;

    if (searchQuery) {
      filtered = filtered.filter(doc =>
        doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.summary?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    if (selectedFilter !== 'all') {
      filtered = filtered.filter(doc => doc.source_type.toLowerCase() === selectedFilter);
    }

    return filtered;
  }, [documents, searchQuery, selectedFilter]);

  // Add mutation for creating documents
  const queryClient = useQueryClient();
  const createDocumentMutation = useMutation({
    mutationFn: async (documentData: any) => {
      try {
        const response = await api.documents.createDocument(documentData);
        return response.document || response;
      } catch (error) {
        console.error('Failed to create document:', error);
        // Fallback behavior for development
        return { 
          id: Date.now(), 
          title: documentData.text.split('\n')[0]?.substring(0, 50) + '...' || 'New Document',
          ...documentData, 
          created_at: new Date().toISOString(), 
          updated_at: new Date().toISOString(),
          file_size: documentData.text.length,
          task_count: 0,
          tags: []
        };
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleDocumentSelect = (id: number) => {
    const document = filteredDocuments.find(doc => doc.id === id);
    if (document) {
      setSelectedDocument(document);
    }
  };

  const handleDocumentEdit = (id: number) => {
    // TODO: Open edit modal
    console.log('Edit document:', id);
  };

  const handleDocumentDelete = (id: number) => {
    // TODO: Delete document
    console.log('Delete document:', id);
  };

  const handleAddDocument = () => {
    setShowAddModal(true);
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      "h-full flex flex-col bg-background transition-all duration-300",
      selectedDocument && "mr-96"
    )}>
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border bg-card/50">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-foreground">Documents</h1>
              <p className="text-muted-foreground">
                Manage your document library and content
              </p>
            </div>
            <button
              onClick={handleAddDocument}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              Add Document
            </button>
          </div>

          {/* Search and Filters */}
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value)}
              className="px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="all">All Types</option>
              <option value="document">Documents</option>
              <option value="notes">Notes</option>
              <option value="web">Web Content</option>
            </select>
          </div>
        </div>
      </div>

      {/* Documents Grid */}
      <div className="flex-1 overflow-auto p-6">
        {filteredDocuments.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <FileText className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">
              No documents found
            </h3>
            <p className="text-muted-foreground mb-6 max-w-md">
              {searchQuery || selectedFilter !== 'all'
                ? 'No documents match your current filters. Try adjusting your search criteria.'
                : 'Get started by adding your first document to the library.'}
            </p>
            <button
              onClick={handleAddDocument}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              Add First Document
            </button>
          </div>
        ) : (
          <motion.div
            layout
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            <AnimatePresence>
              {filteredDocuments.map((document) => (
                <DocumentCard
                  key={document.id}
                  document={document}
                  onSelect={handleDocumentSelect}
                  onEdit={handleDocumentEdit}
                  onDelete={handleDocumentDelete}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>

      {/* Add Document Modal */}
      {showAddModal && (
        <DocumentFormModal
          onClose={() => setShowAddModal(false)}
          onSave={async (documentData) => {
            await createDocumentMutation.mutateAsync(documentData);
            setShowAddModal(false);
          }}
        />
      )}

      {/* Document Detail Panel */}
      <AnimatePresence>
        {selectedDocument && (
          <DocumentDetailPanel
            document={selectedDocument}
            onClose={() => setSelectedDocument(null)}
            onEdit={handleDocumentEdit}
            onDelete={handleDocumentDelete}
            navigate={navigate}
          />
        )}
      </AnimatePresence>
    </div>
  );
};
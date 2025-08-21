import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
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

export const DocumentsPage: React.FC = () => {
  const { setCurrentView } = useUI();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);

  React.useEffect(() => {
    setCurrentView('documents');
  }, [setCurrentView]);

  // Fetch documents (using resources API for now)
  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents', searchQuery, selectedFilter],
    queryFn: async () => {
      // TODO: Use proper documents API when available
      // For now, mock some data
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

  const handleDocumentSelect = (id: number) => {
    navigate(`/documents/${id}`);
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
    <div className="h-full flex flex-col bg-background">
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

      {/* Add Document Modal - TODO: Implement */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Add Document</h2>
            <p className="text-muted-foreground mb-4">
              Document upload functionality will be implemented here.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
import React, { useState, useCallback, useMemo } from 'react';
import { Search, Bell, User, Menu, X, Plus, Filter, Grid3X3, List, 
         Calendar, Tag, Users, FileText, MessageCircle, Upload, 
         Download, Eye, Trash2, Send, Paperclip, Sun, Moon,
         Home, CheckSquare, FileIcon, BarChart3, Settings,
         Clock, AlertCircle, CheckCircle, Pause, Play } from 'lucide-react';

// TypeScript Types
interface Task {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done' | 'blocked';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignee: User;
  createdDate: string;
  dueDate: string;
  tags: string[];
  progress: number;
  documents: Document[];
  qaHistory: QAMessage[];
}

interface User {
  id: string;
  name: string;
  avatar: string;
  role: string;
}

interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadDate: string;
  url: string;
  thumbnail?: string;
}

interface QAMessage {
  id: string;
  type: 'question' | 'answer';
  content: string;
  timestamp: string;
  user?: User;
  references?: string[];
}

// Mock Data
const mockUsers: User[] = [
  { id: '1', name: 'John Doe', avatar: '👨‍💻', role: 'Developer' },
  { id: '2', name: 'Jane Smith', avatar: '👩‍🎨', role: 'Designer' },
  { id: '3', name: 'Mike Johnson', avatar: '👨‍💼', role: 'Manager' },
];

const mockTasks: Task[] = [
  {
    id: '1',
    title: 'Implement user authentication system',
    description: 'Set up JWT-based authentication with login, logout, and session management',
    status: 'in_progress',
    priority: 'high',
    assignee: mockUsers[0],
    createdDate: '2024-01-15',
    dueDate: '2024-01-30',
    tags: ['backend', 'security', 'authentication'],
    progress: 65,
    documents: [
      {
        id: 'd1',
        name: 'Authentication Requirements.pdf',
        size: 1024000,
        type: 'application/pdf',
        uploadDate: '2024-01-16',
        url: '#',
        thumbnail: '📄'
      },
      {
        id: 'd2',
        name: 'Login Mockup.png',
        size: 512000,
        type: 'image/png',
        uploadDate: '2024-01-17',
        url: '#',
        thumbnail: '🖼️'
      }
    ],
    qaHistory: [
      {
        id: 'qa1',
        type: 'question',
        content: 'What authentication method should we use?',
        timestamp: '2024-01-16T10:00:00Z',
        user: mockUsers[0]
      },
      {
        id: 'qa2',
        type: 'answer',
        content: 'Based on the requirements document, JWT tokens would be the best choice for this project. It provides good security and scalability.',
        timestamp: '2024-01-16T10:05:00Z',
        references: ['Authentication Requirements.pdf']
      }
    ]
  },
  {
    id: '2',
    title: 'Design user dashboard interface',
    description: 'Create wireframes and high-fidelity designs for the main dashboard',
    status: 'todo',
    priority: 'medium',
    assignee: mockUsers[1],
    createdDate: '2024-01-18',
    dueDate: '2024-02-05',
    tags: ['design', 'ui', 'dashboard'],
    progress: 20,
    documents: [],
    qaHistory: []
  },
  {
    id: '3',
    title: 'Set up CI/CD pipeline',
    description: 'Configure automated testing and deployment pipeline',
    status: 'done',
    priority: 'high',
    assignee: mockUsers[0],
    createdDate: '2024-01-10',
    dueDate: '2024-01-25',
    tags: ['devops', 'automation'],
    progress: 100,
    documents: [],
    qaHistory: []
  }
];

// Utility Components
const Button: React.FC<{
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
}> = ({ variant = 'primary', size = 'md', onClick, children, className = '', disabled = false }) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-lg font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };
  
  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

const Badge: React.FC<{
  variant: 'status' | 'priority' | 'tag';
  value: string;
  className?: string;
}> = ({ variant, value, className = '' }) => {
  const getClasses = () => {
    const base = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
    
    if (variant === 'status') {
      const statusColors = {
        todo: 'bg-gray-100 text-gray-800',
        in_progress: 'bg-blue-100 text-blue-800',
        done: 'bg-green-100 text-green-800',
        blocked: 'bg-red-100 text-red-800'
      };
      return `${base} ${statusColors[value as keyof typeof statusColors]}`;
    }
    
    if (variant === 'priority') {
      const priorityColors = {
        low: 'bg-gray-100 text-gray-800',
        medium: 'bg-yellow-100 text-yellow-800',
        high: 'bg-orange-100 text-orange-800',
        critical: 'bg-red-100 text-red-800'
      };
      return `${base} ${priorityColors[value as keyof typeof priorityColors]}`;
    }
    
    return `${base} bg-blue-100 text-blue-800`;
  };
  
  return <span className={`${getClasses()} ${className}`}>{value}</span>;
};

const Avatar: React.FC<{ user: User; size?: 'sm' | 'md' | 'lg' }> = ({ user, size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-6 h-6 text-sm',
    md: 'w-8 h-8 text-base',
    lg: 'w-10 h-10 text-lg'
  };
  
  return (
    <div className={`${sizeClasses[size]} rounded-full bg-blue-100 flex items-center justify-center font-medium text-blue-600`}>
      {user.avatar}
    </div>
  );
};

// Main App Component
const TaskManagementApp: React.FC = () => {
  // State Management
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [activeTab, setActiveTab] = useState<'info' | 'documents' | 'qa'>('info');
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [newMessage, setNewMessage] = useState('');

  // Filtered tasks based on search and filters
  const filteredTasks = useMemo(() => {
    return mockTasks.filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          task.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
      const matchesPriority = priorityFilter === 'all' || task.priority === priorityFilter;
      
      return matchesSearch && matchesStatus && matchesPriority;
    });
  }, [searchQuery, statusFilter, priorityFilter]);

  // Event Handlers
  const handleTaskSelect = useCallback((task: Task) => {
    setSelectedTask(task);
  }, []);

  const handleSendMessage = useCallback(() => {
    if (!newMessage.trim() || !selectedTask) return;
    
    // Simulate adding a new message
    const newQAMessage: QAMessage = {
      id: `qa_${Date.now()}`,
      type: 'question',
      content: newMessage,
      timestamp: new Date().toISOString(),
      user: mockUsers[0]
    };
    
    // In real app, this would update the backend
    console.log('New message:', newQAMessage);
    setNewMessage('');
  }, [newMessage, selectedTask]);

  const toggleTheme = useCallback(() => {
    setIsDarkMode(prev => !prev);
  }, []);

  // Status icons
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'todo': return <Clock className="w-4 h-4" />;
      case 'in_progress': return <Play className="w-4 h-4" />;
      case 'done': return <CheckCircle className="w-4 h-4" />;
      case 'blocked': return <Pause className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`min-h-screen ${isDarkMode ? 'dark bg-gray-900' : 'bg-gray-50'} transition-colors duration-200`}>
      <div className="flex">
        {/* Sidebar */}
        <div className={`${isSidebarOpen ? 'w-64' : 'w-16'} ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-r transition-all duration-300 flex flex-col h-screen`}>
          <div className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <CheckSquare className="w-5 h-5 text-white" />
              </div>
              {isSidebarOpen && (
                <span className={`font-semibold text-lg ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                  TaskFlow
                </span>
              )}
            </div>
          </div>
          
          <nav className="flex-1 px-4 pb-4">
            <div className="space-y-2">
              {[
                { icon: Home, label: 'Dashboard', active: false },
                { icon: CheckSquare, label: 'Tasks', active: true },
                { icon: FileText, label: 'Documents', active: false },
                { icon: BarChart3, label: 'Analytics', active: false },
                { icon: Settings, label: 'Settings', active: false },
              ].map((item) => (
                <div
                  key={item.label}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                    item.active 
                      ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300' 
                      : `${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'}`
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {isSidebarOpen && <span className="font-medium">{item.label}</span>}
                </div>
              ))}
            </div>
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-b px-6 py-4`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                  className="p-2"
                >
                  <Menu className="w-4 h-4" />
                </Button>
                
                <div className="relative">
                  <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                  <input
                    type="text"
                    placeholder="Search tasks, documents, conversations..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className={`pl-10 pr-4 py-2 w-96 rounded-lg border ${
                      isDarkMode 
                        ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                        : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <Button variant="secondary" size="sm" onClick={toggleTheme} className="p-2">
                  {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </Button>
                
                <Button variant="secondary" size="sm" className="p-2">
                  <Bell className="w-4 h-4" />
                </Button>
                
                <div className="flex items-center gap-2">
                  <Avatar user={mockUsers[0]} />
                  <span className={`font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                    {mockUsers[0].name}
                  </span>
                </div>
              </div>
            </div>
          </header>

          {/* Content Area */}
          <div className="flex-1 flex">
            {/* Task List */}
            <div className={`w-1/3 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-r flex flex-col`}>
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h1 className={`text-xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                    Tasks ({filteredTasks.length})
                  </h1>
                  <Button size="sm">
                    <Plus className="w-4 h-4 mr-2" />
                    New Task
                  </Button>
                </div>
                
                {/* Filters */}
                <div className="flex gap-2 mb-4">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className={`px-3 py-1.5 text-sm rounded-md border ${
                      isDarkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-white border-gray-300 text-gray-900'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  >
                    <option value="all">All Status</option>
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="done">Done</option>
                    <option value="blocked">Blocked</option>
                  </select>
                  
                  <select
                    value={priorityFilter}
                    onChange={(e) => setPriorityFilter(e.target.value)}
                    className={`px-3 py-1.5 text-sm rounded-md border ${
                      isDarkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-white border-gray-300 text-gray-900'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  >
                    <option value="all">All Priority</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex gap-1">
                    <Button
                      variant={viewMode === 'cards' ? 'primary' : 'secondary'}
                      size="sm"
                      onClick={() => setViewMode('cards')}
                      className="p-2"
                    >
                      <Grid3X3 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant={viewMode === 'table' ? 'primary' : 'secondary'}
                      size="sm"
                      onClick={() => setViewMode('table')}
                      className="p-2"
                    >
                      <List className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
              
              {/* Task Cards */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {filteredTasks.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => handleTaskSelect(task)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all hover:shadow-md ${
                      selectedTask?.id === task.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : isDarkMode
                        ? 'border-gray-600 bg-gray-700 hover:border-gray-500'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(task.status)}
                        <Badge variant="status" value={task.status} />
                      </div>
                      <Badge variant="priority" value={task.priority} />
                    </div>
                    
                    <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                      {task.title}
                    </h3>
                    
                    <p className={`text-sm mb-3 line-clamp-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                      {task.description}
                    </p>
                    
                    <div className="flex items-center justify-between mb-3">
                      <Avatar user={task.assignee} size="sm" />
                      <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        Due: {new Date(task.dueDate).toLocaleDateString()}
                      </span>
                    </div>
                    
                    <div className="mb-3">
                      <div className="flex justify-between items-center mb-1">
                        <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                          Progress
                        </span>
                        <span className={`text-xs font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                          {task.progress}%
                        </span>
                      </div>
                      <div className={`w-full h-2 rounded-full ${isDarkMode ? 'bg-gray-600' : 'bg-gray-200'}`}>
                        <div
                          className="h-2 bg-blue-500 rounded-full transition-all"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-1">
                      {task.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="tag" value={tag} />
                      ))}
                      {task.tags.length > 3 && (
                        <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                          +{task.tags.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Task Detail */}
            <div className="flex-1 flex flex-col">
              {selectedTask ? (
                <>
                  {/* Task Header */}
                  <div className={`p-6 border-b ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                    <div className="flex items-center justify-between mb-4">
                      <h1 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                        {selectedTask.title}
                      </h1>
                      <div className="flex gap-2">
                        <Button variant="secondary" size="sm">Edit</Button>
                        <Button variant="danger" size="sm">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    
                    {/* Tabs */}
                    <div className="flex gap-6 border-b border-gray-200 dark:border-gray-700">
                      {[
                        { id: 'info', label: 'Task Info', icon: CheckSquare },
                        { id: 'documents', label: 'Documents', icon: FileText, count: selectedTask.documents.length },
                        { id: 'qa', label: 'Q&A', icon: MessageCircle, count: selectedTask.qaHistory.length },
                      ].map((tab) => (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id as any)}
                          className={`flex items-center gap-2 pb-3 border-b-2 transition-colors ${
                            activeTab === tab.id
                              ? 'border-blue-500 text-blue-600'
                              : `border-transparent ${isDarkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'}`
                          }`}
                        >
                          <tab.icon className="w-4 h-4" />
                          <span className="font-medium">{tab.label}</span>
                          {tab.count !== undefined && (
                            <span className={`px-2 py-0.5 text-xs rounded-full ${
                              activeTab === tab.id
                                ? 'bg-blue-100 text-blue-600'
                                : isDarkMode
                                ? 'bg-gray-700 text-gray-300'
                                : 'bg-gray-100 text-gray-600'
                            }`}>
                              {tab.count}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Tab Content */}
                  <div className="flex-1 overflow-y-auto">
                    {activeTab === 'info' && (
                      <div className="p-6 space-y-6">
                        <div className="grid grid-cols-2 gap-6">
                          <div>
                            <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                              Description
                            </label>
                            <textarea
                              value={selectedTask.description}
                              readOnly
                              className={`w-full p-3 rounded-lg border ${
                                isDarkMode 
                                  ? 'bg-gray-700 border-gray-600 text-white' 
                                  : 'bg-gray-50 border-gray-300 text-gray-900'
                              } resize-none`}
                              rows={4}
                            />
                          </div>
                          
                          <div className="space-y-4">
                            <div>
                              <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                Status
                              </label>
                              <div className="flex items-center gap-2">
                                {getStatusIcon(selectedTask.status)}
                                <Badge variant="status" value={selectedTask.status} />
                              </div>
                            </div>
                            
                            <div>
                              <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                Priority
                              </label>
                              <Badge variant="priority" value={selectedTask.priority} />
                            </div>
                            
                            <div>
                              <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                Assignee
                              </label>
                              <div className="flex items-center gap-2">
                                <Avatar user={selectedTask.assignee} />
                                <span className={isDarkMode ? 'text-white' : 'text-gray-900'}>
                                  {selectedTask.assignee.name}
                                </span>
                              </div>
                            </div>
                            
                            <div>
                              <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                Due Date
                              </label>
                              <div className="flex items-center gap-2">
                                <Calendar className="w-4 h-4 text-gray-500" />
                                <span className={isDarkMode ? 'text-white' : 'text-gray-900'}>
                                  {new Date(selectedTask.dueDate).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div>
                          <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                            Progress ({selectedTask.progress}%)
                          </label>
                          <div className={`w-full h-3 rounded-full ${isDarkMode ? 'bg-gray-600' : 'bg-gray-200'}`}>
                            <div
                              className="h-3 bg-blue-500 rounded-full transition-all"
                              style={{ width: `${selectedTask.progress}%` }}
                            />
                          </div>
                        </div>
                        
                        <div>
                          <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                            Tags
                          </label>
                          <div className="flex flex-wrap gap-2">
                            {selectedTask.tags.map((tag) => (
                              <Badge key={tag} variant="tag" value={tag} />
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {activeTab === 'documents' && (
                      <div className="p-6">
                        {/* Upload Area */}
                        <div className={`border-2 border-dashed rounded-xl p-8 text-center mb-6 ${
                          isDarkMode 
                            ? 'border-gray-600 bg-gray-700/50' 
                            : 'border-gray-300 bg-gray-50'
                        }`}>
                          <Upload className={`w-12 h-12 mx-auto mb-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                          <p className={`text-lg font-medium mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            Drop files here or click to upload
                          </p>
                          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                            Support for PDF, DOC, XLSX, PNG, JPG files up to 10MB
                          </p>
                          <Button className="mt-4">
                            <Upload className="w-4 h-4 mr-2" />
                            Choose Files
                          </Button>
                        </div>

                        {/* Document List */}
                        <div className="space-y-3">
                          {selectedTask.documents.map((doc) => (
                            <div
                              key={doc.id}
                              className={`p-4 rounded-lg border ${
                                isDarkMode 
                                  ? 'border-gray-600 bg-gray-700' 
                                  : 'border-gray-200 bg-white'
                              } hover:shadow-md transition-shadow`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="text-2xl">{doc.thumbnail}</div>
                                  <div>
                                    <h4 className={`font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                      {doc.name}
                                    </h4>
                                    <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                                      {formatFileSize(doc.size)} • Uploaded {new Date(doc.uploadDate).toLocaleDateString()}
                                    </p>
                                  </div>
                                </div>
                                <div className="flex gap-2">
                                  <Button variant="secondary" size="sm">
                                    <Eye className="w-4 h-4" />
                                  </Button>
                                  <Button variant="secondary" size="sm">
                                    <Download className="w-4 h-4" />
                                  </Button>
                                  <Button variant="danger" size="sm">
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {activeTab === 'qa' && (
                      <div className="flex flex-col h-full">
                        {/* Messages */}
                        <div className="flex-1 p-6 space-y-4 overflow-y-auto">
                          {selectedTask.qaHistory.map((message) => (
                            <div
                              key={message.id}
                              className={`flex gap-3 ${
                                message.type === 'answer' ? 'justify-end' : 'justify-start'
                              }`}
                            >
                              {message.type === 'question' && message.user && (
                                <Avatar user={message.user} size="sm" />
                              )}
                              <div
                                className={`max-w-2xl p-4 rounded-xl ${
                                  message.type === 'answer'
                                    ? isDarkMode
                                      ? 'bg-blue-900/50 text-blue-100'
                                      : 'bg-blue-100 text-blue-900'
                                    : isDarkMode
                                    ? 'bg-gray-700 text-white'
                                    : 'bg-white text-gray-900 border border-gray-200'
                                }`}
                              >
                                <p className="mb-2">{message.content}</p>
                                {message.references && (
                                  <div className="mt-2 pt-2 border-t border-current border-opacity-20">
                                    <p className="text-xs opacity-75 mb-1">References:</p>
                                    {message.references.map((ref, index) => (
                                      <span key={index} className="text-xs opacity-75 underline">
                                        {ref}
                                      </span>
                                    ))}
                                  </div>
                                )}
                                <div className="flex justify-between items-center mt-2">
                                  {message.user && (
                                    <span className="text-xs opacity-75">
                                      {message.user.name}
                                    </span>
                                  )}
                                  <span className="text-xs opacity-75">
                                    {new Date(message.timestamp).toLocaleTimeString()}
                                  </span>
                                </div>
                              </div>
                              {message.type === 'answer' && (
                                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                                  <span className="text-white text-sm font-bold">AI</span>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>

                        {/* Message Input */}
                        <div className={`p-4 border-t ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'}`}>
                          <div className="flex gap-3">
                            <div className="flex-1">
                              <textarea
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                placeholder="Ask a question about this task..."
                                className={`w-full p-3 rounded-lg border resize-none ${
                                  isDarkMode 
                                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                                    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                                } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                                rows={2}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSendMessage();
                                  }
                                }}
                              />
                            </div>
                            <div className="flex flex-col gap-2">
                              <Button variant="secondary" size="sm" className="p-2">
                                <Paperclip className="w-4 h-4" />
                              </Button>
                              <Button onClick={handleSendMessage} disabled={!newMessage.trim()} className="p-2">
                                <Send className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <CheckSquare className={`w-16 h-16 mx-auto mb-4 ${isDarkMode ? 'text-gray-600' : 'text-gray-400'}`} />
                    <h2 className={`text-xl font-semibold mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                      Select a task to view details
                    </h2>
                    <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Choose a task from the list to see its information, documents, and Q&A history.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskManagementApp;
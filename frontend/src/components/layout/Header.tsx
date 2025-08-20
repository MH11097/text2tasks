import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search,
  Bell,
  Settings,
  Moon,
  Sun,
  Monitor,
  Menu,
  User,
  LogOut,
  Palette,
  Command,
  Plus,
} from 'lucide-react';

import { useUI, useTheme, useSearch } from '@/stores/app-store';
import { cn } from '@/utils/cn';

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar, notifications } = useUI();
  const { mode, setMode, getEffectiveTheme } = useTheme();
  const { globalSearchQuery, setGlobalSearchQuery, recentSearches } = useSearch();
  
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showThemeMenu, setShowThemeMenu] = useState(false);
  const [showSearchSuggestions, setShowSearchSuggestions] = useState(false);

  const currentTheme = getEffectiveTheme();
  const unreadNotifications = notifications.filter(n => !n.read).length;

  const handleSearch = (query: string) => {
    if (!query.trim()) return;
    
    // Add to recent searches
    const { addRecentSearch } = useSearch.getState();
    addRecentSearch(query);
    
    // Navigate to search results or perform search
    navigate(`/search?q=${encodeURIComponent(query)}`);
    setShowSearchSuggestions(false);
  };

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'new-task':
        navigate('/tasks/new');
        break;
      case 'new-document':
        navigate('/ingest');
        break;
      case 'ask-question':
        navigate('/qa');
        break;
      default:
        break;
    }
  };

  const themeOptions = [
    { value: 'light', label: 'Light', icon: Sun },
    { value: 'dark', label: 'Dark', icon: Moon },
    { value: 'system', label: 'System', icon: Monitor },
  ];

  return (
    <header className="bg-card border-b border-border px-4 py-3 flex items-center justify-between relative z-30">
      {/* Left section */}
      <div className="flex items-center gap-4">
        {/* Sidebar toggle */}
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-muted rounded-md transition-colors"
          aria-label="Toggle sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Global search */}
        <div className="relative">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              id="global-search"
              type="text"
              value={globalSearchQuery}
              onChange={(e) => {
                setGlobalSearchQuery(e.target.value);
                setShowSearchSuggestions(true);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSearch(globalSearchQuery);
                } else if (e.key === 'Escape') {
                  setShowSearchSuggestions(false);
                }
              }}
              onFocus={() => setShowSearchSuggestions(true)}
              placeholder="Search tasks, documents, conversations..."
              className="pl-10 pr-20 py-2 w-96 max-w-lg bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            />
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 text-xs bg-muted border border-border rounded">
                ⌘K
              </kbd>
            </div>
          </div>

          {/* Search suggestions */}
          {showSearchSuggestions && (globalSearchQuery || recentSearches.length > 0) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-full left-0 right-0 mt-2 bg-popover border border-border rounded-lg shadow-lg z-50"
            >
              <div className="p-2">
                {globalSearchQuery && (
                  <button
                    onClick={() => handleSearch(globalSearchQuery)}
                    className="w-full text-left px-3 py-2 hover:bg-muted rounded-md flex items-center gap-3"
                  >
                    <Search className="h-4 w-4" />
                    <span>Search for "{globalSearchQuery}"</span>
                  </button>
                )}
                
                {recentSearches.length > 0 && (
                  <>
                    <div className="px-3 py-1 text-xs text-muted-foreground border-t border-border mt-2 pt-2">
                      Recent searches
                    </div>
                    {recentSearches.slice(0, 5).map((search, index) => (
                      <button
                        key={index}
                        onClick={() => handleSearch(search)}
                        className="w-full text-left px-3 py-2 hover:bg-muted rounded-md text-sm"
                      >
                        {search}
                      </button>
                    ))}
                  </>
                )}
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-2">
        {/* Quick actions */}
        <div className="hidden md:flex items-center gap-1">
          <button
            onClick={() => handleQuickAction('new-task')}
            className="p-2 hover:bg-muted rounded-md transition-colors"
            title="New Task (Ctrl+N)"
          >
            <Plus className="h-4 w-4" />
          </button>
          
          <button
            onClick={() => handleQuickAction('ask-question')}
            className="p-2 hover:bg-muted rounded-md transition-colors"
            title="Ask Question"
          >
            <Command className="h-4 w-4" />
          </button>
        </div>

        {/* Theme toggle */}
        <div className="relative">
          <button
            onClick={() => setShowThemeMenu(!showThemeMenu)}
            className="p-2 hover:bg-muted rounded-md transition-colors"
            title="Toggle theme"
          >
            {currentTheme === 'dark' ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
          </button>

          {showThemeMenu && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="absolute right-0 top-full mt-2 bg-popover border border-border rounded-lg shadow-lg p-1 z-50 min-w-32"
            >
              {themeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => {
                    setMode(option.value as any);
                    setShowThemeMenu(false);
                  }}
                  className={cn(
                    'w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors',
                    mode === option.value && 'bg-muted'
                  )}
                >
                  <option.icon className="h-4 w-4" />
                  {option.label}
                  {mode === option.value && (
                    <div className="ml-auto w-1.5 h-1.5 bg-primary rounded-full" />
                  )}
                </button>
              ))}
            </motion.div>
          )}
        </div>

        {/* Notifications */}
        <button
          onClick={() => navigate('/notifications')}
          className="p-2 hover:bg-muted rounded-md transition-colors relative"
          title="Notifications"
        >
          <Bell className="h-4 w-4" />
          {unreadNotifications > 0 && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-1 -right-1 bg-destructive text-destructive-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center"
            >
              {unreadNotifications > 9 ? '9+' : unreadNotifications}
            </motion.div>
          )}
        </button>

        {/* Settings */}
        <button
          onClick={() => navigate('/settings')}
          className="p-2 hover:bg-muted rounded-md transition-colors"
          title="Settings"
        >
          <Settings className="h-4 w-4" />
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="p-2 hover:bg-muted rounded-md transition-colors"
            title="User menu"
          >
            <User className="h-4 w-4" />
          </button>

          {showUserMenu && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="absolute right-0 top-full mt-2 bg-popover border border-border rounded-lg shadow-lg p-1 z-50 min-w-48"
            >
              <div className="px-3 py-2 border-b border-border">
                <div className="font-medium">Current User</div>
                <div className="text-sm text-muted-foreground">user@example.com</div>
              </div>
              
              <button
                onClick={() => {
                  navigate('/profile');
                  setShowUserMenu(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors"
              >
                <User className="h-4 w-4" />
                Profile
              </button>
              
              <button
                onClick={() => {
                  navigate('/settings');
                  setShowUserMenu(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors"
              >
                <Settings className="h-4 w-4" />
                Settings
              </button>
              
              <div className="border-t border-border my-1" />
              
              <button
                onClick={() => {
                  // Handle logout
                  setShowUserMenu(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors text-destructive"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </motion.div>
          )}
        </div>
      </div>

      {/* Click outside handlers */}
      {showUserMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowUserMenu(false)}
        />
      )}
      {showThemeMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowThemeMenu(false)}
        />
      )}
      {showSearchSuggestions && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowSearchSuggestions(false)}
        />
      )}
    </header>
  );
};
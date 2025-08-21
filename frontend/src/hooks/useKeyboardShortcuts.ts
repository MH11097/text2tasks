import { useEffect, useCallback, useRef } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  description: string;
  action: () => void;
  category?: string;
  preventDefault?: boolean;
}

export interface KeyboardShortcutGroup {
  [key: string]: KeyboardShortcut[];
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[], enabled = true) => {
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return;

    // Don't trigger shortcuts when user is typing in inputs
    if (
      event.target instanceof HTMLInputElement ||
      event.target instanceof HTMLTextAreaElement ||
      event.target instanceof HTMLSelectElement ||
      (event.target as HTMLElement)?.contentEditable === 'true'
    ) {
      return;
    }

    const activeShortcuts = shortcutsRef.current;

    for (const shortcut of activeShortcuts) {
      const keyMatch = shortcut.key.toLowerCase() === event.key.toLowerCase();
      const ctrlMatch = !!shortcut.ctrl === (event.ctrlKey || event.metaKey);
      const shiftMatch = !!shortcut.shift === event.shiftKey;
      const altMatch = !!shortcut.alt === event.altKey;
      const metaMatch = !!shortcut.meta === event.metaKey;

      if (keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch) {
        if (shortcut.preventDefault !== false) {
          event.preventDefault();
        }
        shortcut.action();
        break;
      }
    }
  }, [enabled]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
};

export const useGlobalKeyboardShortcuts = () => {
  const shortcuts: KeyboardShortcut[] = [
    {
      key: 'k',
      ctrl: true,
      description: 'Open quick search',
      category: 'Navigation',
      action: () => {
        const searchInput = document.getElementById('global-search');
        searchInput?.focus();
      }
    },
    {
      key: '/',
      ctrl: true,
      description: 'Open command palette',
      category: 'Navigation',
      action: () => {
        console.log('Open command palette');
        // TODO: Implement command palette
      }
    },
    {
      key: 'n',
      ctrl: true,
      description: 'Create new task',
      category: 'Actions',
      action: () => {
        const createButton = document.querySelector('[data-action="create-task"]') as HTMLElement;
        createButton?.click();
      }
    },
    {
      key: 'a',
      ctrl: true,
      shift: true,
      description: 'Toggle analytics dashboard',
      category: 'Views',
      action: () => {
        const analyticsButton = document.querySelector('[data-action="toggle-analytics"]') as HTMLElement;
        analyticsButton?.click();
      }
    },
    {
      key: 's',
      ctrl: true,
      shift: true,
      description: 'Toggle smart automation',
      category: 'Views',
      action: () => {
        const automationButton = document.querySelector('[data-action="toggle-automation"]') as HTMLElement;
        automationButton?.click();
      }
    },
    {
      key: 'r',
      ctrl: true,
      shift: true,
      description: 'Toggle task relationships',
      category: 'Views',
      action: () => {
        const relationshipsButton = document.querySelector('[data-action="toggle-relationships"]') as HTMLElement;
        relationshipsButton?.click();
      }
    },
    {
      key: 'p',
      ctrl: true,
      shift: true,
      description: 'Toggle productivity features',
      category: 'Views',
      action: () => {
        const productivityButton = document.querySelector('[data-action="toggle-productivity"]') as HTMLElement;
        productivityButton?.click();
      }
    },
    {
      key: '1',
      ctrl: true,
      description: 'Switch to Tasks page',
      category: 'Navigation',
      action: () => {
        window.location.hash = '/tasks';
      }
    },
    {
      key: '2',
      ctrl: true,
      description: 'Switch to Documents page',
      category: 'Navigation',
      action: () => {
        window.location.hash = '/documents';
      }
    },
    {
      key: '3',
      ctrl: true,
      description: 'Switch to Q&A page',
      category: 'Navigation',
      action: () => {
        window.location.hash = '/qa';
      }
    },
    {
      key: 'g',
      ctrl: true,
      description: 'Toggle grid/list view',
      category: 'Views',
      action: () => {
        const viewToggle = document.querySelector('[data-action="toggle-view"]') as HTMLElement;
        viewToggle?.click();
      }
    },
    {
      key: 'Escape',
      description: 'Close modals and overlays',
      category: 'Navigation',
      action: () => {
        const closeButtons = document.querySelectorAll('[data-action="close"], [aria-label="close"]');
        const lastCloseButton = closeButtons[closeButtons.length - 1] as HTMLElement;
        lastCloseButton?.click();
      }
    },
    {
      key: '?',
      ctrl: true,
      description: 'Show keyboard shortcuts help',
      category: 'Help',
      action: () => {
        console.log('Show keyboard shortcuts help');
        // TODO: Implement help modal
      }
    }
  ];

  useKeyboardShortcuts(shortcuts);

  return shortcuts;
};

// Hook for managing shortcuts help modal
export const useKeyboardShortcutsHelp = () => {
  const shortcuts = useGlobalKeyboardShortcuts();

  const groupedShortcuts: KeyboardShortcutGroup = shortcuts.reduce((acc, shortcut) => {
    const category = shortcut.category || 'General';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(shortcut);
    return acc;
  }, {} as KeyboardShortcutGroup);

  const formatShortcut = (shortcut: KeyboardShortcut): string => {
    const parts: string[] = [];
    
    if (shortcut.ctrl) parts.push('Ctrl');
    if (shortcut.shift) parts.push('Shift');
    if (shortcut.alt) parts.push('Alt');
    if (shortcut.meta) parts.push('Cmd');
    
    parts.push(shortcut.key.toUpperCase());
    
    return parts.join(' + ');
  };

  return {
    shortcuts: groupedShortcuts,
    formatShortcut
  };
};
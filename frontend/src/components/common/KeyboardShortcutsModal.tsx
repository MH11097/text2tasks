import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Keyboard, Zap } from 'lucide-react';
import { useKeyboardShortcutsHelp } from '@/hooks/useKeyboardShortcuts';
import { cn } from '@/utils/cn';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({
  isOpen,
  onClose
}) => {
  const { shortcuts, formatShortcut } = useKeyboardShortcutsHelp();

  const categoryIcons = {
    Navigation: '🧭',
    Actions: '⚡',
    Views: '👁️',
    Help: '❓',
    General: '⚙️'
  };

  const categoryColors = {
    Navigation: 'border-blue-200 bg-blue-50 dark:border-blue-700 dark:bg-blue-950',
    Actions: 'border-green-200 bg-green-50 dark:border-green-700 dark:bg-green-950',
    Views: 'border-purple-200 bg-purple-50 dark:border-purple-700 dark:bg-purple-950',
    Help: 'border-orange-200 bg-orange-50 dark:border-orange-700 dark:bg-orange-950',
    General: 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-950'
  };

  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-border bg-muted/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                  <Keyboard className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-foreground">Keyboard Shortcuts</h2>
                  <p className="text-sm text-muted-foreground">
                    Master your workflow with these power-user shortcuts
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-muted transition-colors"
                data-action="close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Object.entries(shortcuts).map(([category, categoryShortcuts]) => (
                  <motion.div
                    key={category}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Object.keys(shortcuts).indexOf(category) * 0.1 }}
                    className={cn(
                      'border rounded-xl p-4',
                      categoryColors[category as keyof typeof categoryColors] || categoryColors.General
                    )}
                  >
                    <div className="flex items-center gap-2 mb-4">
                      <span className="text-lg">
                        {categoryIcons[category as keyof typeof categoryIcons] || categoryIcons.General}
                      </span>
                      <h3 className="font-semibold text-foreground">{category}</h3>
                      <span className="text-xs text-muted-foreground bg-background px-2 py-1 rounded-full">
                        {categoryShortcuts.length} shortcuts
                      </span>
                    </div>
                    
                    <div className="space-y-3">
                      {categoryShortcuts.map((shortcut, index) => (
                        <motion.div
                          key={`${category}-${index}`}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: (Object.keys(shortcuts).indexOf(category) * 0.1) + (index * 0.05) }}
                          className="flex items-center justify-between py-2 px-3 bg-background/50 rounded-lg border border-border/50"
                        >
                          <span className="text-sm text-foreground flex-1">
                            {shortcut.description}
                          </span>
                          <div className="flex items-center gap-1 ml-4">
                            {formatShortcut(shortcut).split(' + ').map((key, keyIndex) => (
                              <React.Fragment key={keyIndex}>
                                {keyIndex > 0 && (
                                  <span className="text-xs text-muted-foreground mx-1">+</span>
                                )}
                                <kbd className="px-2 py-1 text-xs font-mono font-medium bg-muted text-muted-foreground border border-border rounded">
                                  {key}
                                </kbd>
                              </React.Fragment>
                            ))}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Tips Section */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="mt-8 p-4 bg-primary/5 border border-primary/20 rounded-xl"
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                    <Zap className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground mb-2">Pro Tips</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Shortcuts work globally except when typing in text fields</li>
                      <li>• Use <kbd className="px-1 py-0.5 text-xs bg-muted rounded font-mono">Ctrl + ?</kbd> to quickly open this help anytime</li>
                      <li>• Combine shortcuts for powerful workflows (e.g., <kbd className="px-1 py-0.5 text-xs bg-muted rounded font-mono">Ctrl + N</kbd> then start typing)</li>
                      <li>• Most buttons show their shortcuts in tooltips when you hover</li>
                    </ul>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-muted/50">
              <div className="text-sm text-muted-foreground">
                Press <kbd className="px-2 py-1 text-xs bg-background border rounded font-mono">Esc</kbd> to close
              </div>
              <div className="text-xs text-muted-foreground">
                Total: {Object.values(shortcuts).flat().length} shortcuts available
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
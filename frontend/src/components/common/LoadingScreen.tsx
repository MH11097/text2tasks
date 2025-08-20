import React from 'react';
import { motion } from 'framer-motion';
import { CheckSquare, Loader2 } from 'lucide-react';

interface LoadingScreenProps {
  message?: string;
  submessage?: string;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message = 'Loading AI Work OS...',
  submessage = 'Professional Task Management',
}) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary via-primary/90 to-purple-600 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="text-center space-y-8"
      >
        {/* Logo and branding */}
        <motion.div
          initial={{ y: -20 }}
          animate={{ y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="space-y-4"
        >
          <div className="flex justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              className="p-4 bg-white/10 backdrop-blur-sm rounded-2xl border border-white/20"
            >
              <CheckSquare className="h-12 w-12 text-white" />
            </motion.div>
          </div>
          
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              AI Work OS
            </h1>
            <p className="text-white/80 text-lg">
              {submessage}
            </p>
          </div>
        </motion.div>

        {/* Loading animation */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="space-y-4"
        >
          <div className="flex items-center justify-center gap-3 text-white">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-lg font-medium">{message}</span>
          </div>
          
          {/* Progress bar */}
          <div className="w-64 mx-auto">
            <div className="h-1 bg-white/20 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: '100%' }}
                transition={{ duration: 2, ease: 'easeInOut' }}
                className="h-full bg-white/60 rounded-full"
              />
            </div>
          </div>
        </motion.div>

        {/* Feature highlights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="space-y-2 text-white/70 text-sm max-w-md"
        >
          <div className="flex items-center justify-center gap-2">
            <div className="w-1 h-1 bg-white/60 rounded-full" />
            <span>Task Hierarchy Management</span>
          </div>
          <div className="flex items-center justify-center gap-2">
            <div className="w-1 h-1 bg-white/60 rounded-full" />
            <span>AI-Powered Q&A</span>
          </div>
          <div className="flex items-center justify-center gap-2">
            <div className="w-1 h-1 bg-white/60 rounded-full" />
            <span>Document Intelligence</span>
          </div>
        </motion.div>

        {/* Version info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-white/50 text-xs"
        >
          Version 0.1.0
        </motion.div>
      </motion.div>
    </div>
  );
};
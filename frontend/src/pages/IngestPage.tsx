import React from 'react';
import { motion } from 'framer-motion';

export const IngestPage: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6"
    >
      <h1 className="text-3xl font-bold text-foreground mb-6">Add Content</h1>
      <div className="bg-card border border-border rounded-lg p-8 text-center">
        <p className="text-muted-foreground">Document ingestion interface coming soon...</p>
      </div>
    </motion.div>
  );
};
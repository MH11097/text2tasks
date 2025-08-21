import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface ActionItem {
  title: string;
  owner?: string;
  due?: string;
  blockers: string[];
  project_hint?: string;
}

interface IngestResponse {
  document_id: string;
  summary: string;
  actions: ActionItem[];
}

export const IngestPage: React.FC = () => {
  const [text, setText] = useState('');
  const [source, setSource] = useState('document');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch('/api/v1/ingest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          source
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data: IngestResponse = await res.json();
      setResponse(data);
      setText('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 max-w-4xl mx-auto"
    >
      <h1 className="text-3xl font-bold text-foreground mb-6">Add Content</h1>
      
      <div className="grid gap-6">
        {/* Input Form */}
        <div className="bg-card border border-border rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="source" className="block text-sm font-medium text-foreground mb-2">
                Source Type
              </label>
              <select
                id="source"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="w-full p-2 bg-background border border-border rounded-md text-foreground"
              >
                <option value="document">Document</option>
                <option value="email">Email</option>
                <option value="meeting">Meeting</option>
                <option value="note">Note</option>
                <option value="chat">Chat</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="text" className="block text-sm font-medium text-foreground mb-2">
                Content
              </label>
              <textarea
                id="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste your content here..."
                className="w-full h-40 p-4 bg-background border border-border rounded-md text-foreground resize-none"
                required
                minLength={1}
                maxLength={50000}
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading || !text.trim()}
              className="w-full bg-primary text-primary-foreground py-2 px-4 rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Processing...' : 'Process Content'}
            </button>
          </form>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-destructive/10 border border-destructive rounded-lg p-4">
            <p className="text-destructive font-medium">Error:</p>
            <p className="text-destructive">{error}</p>
          </div>
        )}

        {/* Results Display */}
        {response && (
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Results</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Document ID</h3>
                <p className="text-foreground font-mono text-sm bg-background p-2 rounded border">
                  {response.document_id}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Summary</h3>
                <p className="text-foreground bg-background p-3 rounded border">
                  {response.summary}
                </p>
              </div>
              
              {response.actions.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">
                    Generated Tasks ({response.actions.length})
                  </h3>
                  <div className="space-y-2">
                    {response.actions.map((action, index) => (
                      <div key={index} className="bg-background border border-border rounded p-3">
                        <div className="font-medium text-foreground">{action.title}</div>
                        {action.owner && (
                          <div className="text-sm text-muted-foreground mt-1">
                            Owner: {action.owner}
                          </div>
                        )}
                        {action.due && (
                          <div className="text-sm text-muted-foreground mt-1">
                            Due: {action.due}
                          </div>
                        )}
                        {action.blockers.length > 0 && (
                          <div className="text-sm text-muted-foreground mt-1">
                            Blockers: {action.blockers.join(', ')}
                          </div>
                        )}
                        {action.project_hint && (
                          <div className="text-sm text-muted-foreground mt-1">
                            Project: {action.project_hint}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};
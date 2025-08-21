import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { CheckSquare, X, Search } from 'lucide-react';
import { api } from '@/services/api';
import { AskResponse } from '@/types/api';

interface Task {
  id: number;
  title: string;
  status: string;
  owner?: string;
  due_date?: string;
}

export const QAPage: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(6);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<Array<{question: string, response: AskResponse}>>([]);
  const [selectedTasks, setSelectedTasks] = useState<number[]>([]);
  const [taskSearchQuery, setTaskSearchQuery] = useState('');

  // Fetch available tasks
  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => api.tasks.getTasks(),
  });

  // Filter tasks based on search query
  const filteredTasks = tasks.filter(task =>
    task.title.toLowerCase().includes(taskSearchQuery.toLowerCase()) ||
    task.owner?.toLowerCase().includes(taskSearchQuery.toLowerCase())
  );

  const handleTaskToggle = (taskId: number) => {
    setSelectedTasks(prev =>
      prev.includes(taskId)
        ? prev.filter(id => id !== taskId)
        : [...prev, taskId]
    );
  };

  const removeSelectedTask = (taskId: number) => {
    setSelectedTasks(prev => prev.filter(id => id !== taskId));
  };

  const getSelectedTasksDisplay = () => {
    return tasks.filter(task => selectedTasks.includes(task.id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Use the API client and include selected tasks if any
      const askData = {
        question,
        top_k: topK,
        ...(selectedTasks.length > 0 && { task_ids: selectedTasks })
      };

      const data = await api.qa.ask(askData);
      
      setResponse(data);
      setHistory(prev => [...prev, { 
        question: `${question}${selectedTasks.length > 0 ? ` (with ${selectedTasks.length} task context)` : ''}`, 
        response: data 
      }]);
      setQuestion('');
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
      <h1 className="text-3xl font-bold text-foreground mb-6">Q&A</h1>
      
      <div className="grid gap-6">
        {/* Question Form */}
        <div className="bg-card border border-border rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Task Selection */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Select Tasks for Context (Optional)
              </label>
              
              {/* Selected Tasks Display */}
              {selectedTasks.length > 0 && (
                <div className="mb-3">
                  <div className="flex flex-wrap gap-2">
                    {getSelectedTasksDisplay().map((task) => (
                      <span
                        key={task.id}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-primary/10 text-primary rounded-full text-sm border"
                      >
                        <CheckSquare className="h-3 w-3" />
                        {task.title.substring(0, 30)}{task.title.length > 30 ? '...' : ''}
                        <button
                          type="button"
                          onClick={() => removeSelectedTask(task.id)}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {selectedTasks.length} task{selectedTasks.length > 1 ? 's' : ''} selected for context
                  </p>
                </div>
              )}

              {/* Task Search and Selection */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search tasks to add context..."
                  value={taskSearchQuery}
                  onChange={(e) => setTaskSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-md text-foreground text-sm"
                />
              </div>

              {/* Task Selection Dropdown */}
              {taskSearchQuery && (
                <div className="mt-2 max-h-48 overflow-y-auto border border-border rounded-md bg-background">
                  {filteredTasks.length > 0 ? (
                    filteredTasks.slice(0, 10).map((task) => (
                      <button
                        key={task.id}
                        type="button"
                        onClick={() => {
                          handleTaskToggle(task.id);
                          setTaskSearchQuery(''); // Clear search after selection
                        }}
                        className={`w-full text-left px-3 py-2 hover:bg-muted transition-colors border-b border-border last:border-b-0 ${
                          selectedTasks.includes(task.id) ? 'bg-primary/5' : ''
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <CheckSquare 
                            className={`h-4 w-4 ${
                              selectedTasks.includes(task.id) ? 'text-primary' : 'text-muted-foreground'
                            }`} 
                          />
                          <div>
                            <div className="font-medium text-sm">{task.title}</div>
                            <div className="text-xs text-muted-foreground">
                              Status: {task.status} {task.owner && `• Owner: ${task.owner}`}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="px-3 py-2 text-sm text-muted-foreground">
                      No tasks found matching "{taskSearchQuery}"
                    </div>
                  )}
                </div>
              )}
            </div>

            <div>
              <label htmlFor="question" className="block text-sm font-medium text-foreground mb-2">
                Ask a Question
              </label>
              <input
                type="text"
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="What would you like to know?"
                className="w-full p-3 bg-background border border-border rounded-md text-foreground"
                required
                minLength={3}
                maxLength={1000}
              />
            </div>
            
            <div className="flex items-center space-x-4">
              <div>
                <label htmlFor="topK" className="block text-sm font-medium text-foreground mb-2">
                  Search Depth
                </label>
                <select
                  id="topK"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  className="p-2 bg-background border border-border rounded-md text-foreground"
                >
                  <option value={3}>3 documents</option>
                  <option value={6}>6 documents</option>
                  <option value={9}>9 documents</option>
                  <option value={12}>12 documents</option>
                </select>
              </div>
              
              <button
                type="submit"
                disabled={isLoading || !question.trim()}
                className="bg-primary text-primary-foreground py-2 px-6 rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed mt-6"
              >
                {isLoading ? 'Searching...' : 'Ask'}
              </button>
            </div>
          </form>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-destructive/10 border border-destructive rounded-lg p-4">
            <p className="text-destructive font-medium">Error:</p>
            <p className="text-destructive">{error}</p>
          </div>
        )}

        {/* Current Answer */}
        {response && (
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Answer</h2>
            
            <div className="space-y-4">
              <div className="bg-background p-4 rounded border">
                <p className="text-foreground whitespace-pre-wrap">{response.answer}</p>
              </div>
              
              {response.refs.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">
                    Referenced Documents ({response.refs.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {response.refs.map((ref, index) => (
                      <span
                        key={index}
                        className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded font-mono"
                      >
                        Doc #{ref}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {response.suggested_next_steps.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">
                    Suggested Next Steps
                  </h3>
                  <ul className="space-y-1">
                    {response.suggested_next_steps.map((step, index) => (
                      <li key={index} className="text-sm text-foreground flex items-start">
                        <span className="text-primary mr-2">•</span>
                        {step}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Q&A History */}
        {history.length > 0 && (
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">
              Q&A History ({history.length})
            </h2>
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {history.slice().reverse().map((item, index) => (
                <div key={index} className="border-l-2 border-primary pl-4 py-2">
                  <div className="font-medium text-foreground mb-2">
                    Q: {item.question}
                  </div>
                  <div className="text-sm text-muted-foreground bg-background p-3 rounded">
                    {item.response.answer.substring(0, 200)}
                    {item.response.answer.length > 200 && '...'}
                  </div>
                  {item.response.refs.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {item.response.refs.map((ref, refIndex) => (
                        <span
                          key={refIndex}
                          className="text-xs bg-secondary text-secondary-foreground px-1 py-0.5 rounded font-mono"
                        >
                          #{ref}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};
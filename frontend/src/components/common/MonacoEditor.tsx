import React, { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { useTheme } from '@/stores/app-store';

interface MonacoEditorProps {
  value: string;
  onChange: (value: string | undefined) => void;
  language?: string;
  height?: string | number;
  readOnly?: boolean;
  placeholder?: string;
  className?: string;
}

export const MonacoEditor: React.FC<MonacoEditorProps> = ({
  value,
  onChange,
  language = 'markdown',
  height = '400px',
  readOnly = false,
  placeholder = 'Enter content...',
  className = '',
}) => {
  const { getEffectiveTheme } = useTheme();
  const editorRef = useRef<any>(null);

  const theme = getEffectiveTheme() === 'dark' ? 'vs-dark' : 'vs-light';

  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;

    // Configure editor options
    editor.updateOptions({
      wordWrap: 'on',
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      renderLineHighlight: 'none',
      overviewRulerBorder: false,
      hideCursorInOverviewRuler: true,
      lineNumbers: 'on',
      glyphMargin: false,
      folding: true,
      lineDecorationsWidth: 0,
      lineNumbersMinChars: 3,
      fontSize: 14,
      fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
      tabSize: 2,
      insertSpaces: true,
      automaticLayout: true,
      readOnly,
    });

    // Add placeholder support
    if (!value && placeholder) {
      const decorations = editor.deltaDecorations([], [
        {
          range: new monaco.Range(1, 1, 1, 1),
          options: {
            afterContentClassName: 'monaco-placeholder',
            isWholeLine: false,
          },
        },
      ]);

      // Update placeholder on content change
      editor.onDidChangeModelContent(() => {
        const currentValue = editor.getValue();
        if (!currentValue) {
          editor.deltaDecorations([], [
            {
              range: new monaco.Range(1, 1, 1, 1),
              options: {
                afterContentClassName: 'monaco-placeholder',
                isWholeLine: false,
              },
            },
          ]);
        } else {
          editor.deltaDecorations(decorations, []);
        }
      });
    }

    // Focus editor if not read-only
    if (!readOnly) {
      editor.focus();
    }
  };

  const handleChange = (value: string | undefined) => {
    onChange(value);
  };

  // Inject CSS for placeholder styling
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .monaco-placeholder::after {
        content: "${placeholder}";
        color: #888;
        font-style: italic;
        opacity: 0.6;
        pointer-events: none;
      }
      
      .monaco-editor {
        border-radius: 8px;
      }
      
      .monaco-editor .margin {
        background: transparent;
      }
      
      .monaco-editor .monaco-editor-background {
        background: var(--color-background);
      }
      
      .monaco-editor .current-line {
        background: rgba(255, 255, 255, 0.05);
      }
    `;
    
    document.head.appendChild(style);
    
    return () => {
      document.head.removeChild(style);
    };
  }, [placeholder]);

  return (
    <div className={className}>
      <Editor
        height={height}
        language={language}
        theme={theme}
        value={value}
        onChange={handleChange}
        onMount={handleEditorDidMount}
        options={{
          wordWrap: 'on',
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          renderLineHighlight: 'none',
          overviewRulerBorder: false,
          hideCursorInOverviewRuler: true,
          lineNumbers: 'on',
          glyphMargin: false,
          folding: true,
          lineDecorationsWidth: 0,
          lineNumbersMinChars: 3,
          fontSize: 14,
          fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
          tabSize: 2,
          insertSpaces: true,
          automaticLayout: true,
          readOnly,
        }}
      />
    </div>
  );
};
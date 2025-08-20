// Re-export all types
export * from './api';

// Component prop types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

// Common utility types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredKeys<T, K extends keyof T> = T & Required<Pick<T, K>>;
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// Event handler types
export type ClickHandler = (event: React.MouseEvent) => void;
export type ChangeHandler<T = HTMLInputElement> = (event: React.ChangeEvent<T>) => void;
export type SubmitHandler = (event: React.FormEvent) => void;

// Generic async function type
export type AsyncFunction<T = void, P = unknown[]> = (...args: P extends unknown[] ? P : [P]) => Promise<T>;

// Loading states
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

// Sort direction
export type SortDirection = 'asc' | 'desc';

// Generic key-value pairs
export type KeyValuePair<T = string> = {
  key: string;
  value: T;
  label?: string;
};

// Theme types
export type ThemeMode = 'light' | 'dark' | 'system';

// Screen size breakpoints
export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

// Animation types
export type AnimationDirection = 'up' | 'down' | 'left' | 'right';
export type AnimationDuration = 'fast' | 'normal' | 'slow';

// Position types
export type Position = 'top' | 'bottom' | 'left' | 'right' | 'center';
export type Placement = 
  | 'top' | 'top-start' | 'top-end'
  | 'bottom' | 'bottom-start' | 'bottom-end'
  | 'left' | 'left-start' | 'left-end'
  | 'right' | 'right-start' | 'right-end';

// Size variants
export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type ButtonSize = 'sm' | 'md' | 'lg';
export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

// Color variants
export type ColorVariant = 
  | 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';

// Button variants
export type ButtonVariant = 
  | 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'destructive';

// Input types
export type InputType = 
  | 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search' | 'date' | 'time' | 'datetime-local';

// Modal types
export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: Size;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
}

// Dropdown menu types
export interface DropdownItem {
  id: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
  separator?: boolean;
  children?: DropdownItem[];
  onClick?: () => void;
}

// Tab types
export interface TabItem {
  id: string;
  label: string;
  content: React.ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
  badge?: string | number;
}

// Table types
export interface Column<T> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, record: T, index: number) => React.ReactNode;
}

export interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    onPageChange: (page: number) => void;
    onLimitChange: (limit: number) => void;
  };
  sorting?: {
    key: keyof T | string;
    direction: SortDirection;
    onSort: (key: keyof T | string, direction: SortDirection) => void;
  };
  selection?: {
    selectedKeys: Set<string | number>;
    onSelectionChange: (keys: Set<string | number>) => void;
    getRowKey: (record: T) => string | number;
  };
  className?: string;
}

// Form validation types
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: unknown) => string | null;
}

export interface FieldProps {
  name: string;
  label?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  help?: string;
  rules?: ValidationRule;
}

// Toast notification types
export interface ToastOptions {
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  position?: Position;
  dismissible?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Context menu types
export interface ContextMenuItem {
  id: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  shortcut?: string;
  disabled?: boolean;
  danger?: boolean;
  onClick: () => void;
}

// Virtualization types
export interface VirtualItem {
  index: number;
  start: number;
  size: number;
  end: number;
}

// Drag and drop types
export interface DragItem {
  id: string;
  type: string;
  data: unknown;
}

export interface DropResult {
  source: {
    droppableId: string;
    index: number;
  };
  destination?: {
    droppableId: string;
    index: number;
  };
  type: string;
}

// Error boundary types
export interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
  eventId?: string;
}

// Performance monitoring types
export interface PerformanceMetrics {
  renderTime: number;
  componentCount: number;
  memoryUsage?: number;
  bundleSize?: number;
}

// Accessibility types
export interface A11yProps {
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-selected'?: boolean;
  'aria-disabled'?: boolean;
  role?: string;
  tabIndex?: number;
}
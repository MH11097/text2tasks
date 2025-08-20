# AI Work OS Frontend

A modern, professional React frontend for AI Work OS - a comprehensive task management system with AI-powered features.

## Features

- 🎨 **Modern UI/UX**: Professional design with dark/light theme support
- 📱 **Responsive Design**: Mobile-first approach with touch-friendly interactions
- ⚡ **Performance**: Optimized with Vite, code splitting, and caching
- 🔄 **Real-time Updates**: Live data synchronization (WebSocket support)
- 🎭 **Animations**: Smooth transitions with Framer Motion
- 📊 **State Management**: Zustand for global state, React Query for server state
- 🔒 **Type Safety**: Full TypeScript implementation
- 🧪 **Testing**: Comprehensive test suite with Vitest and Testing Library
- 📴 **PWA Support**: Offline capability and native app experience
- ♿ **Accessibility**: WCAG 2.1 AA compliant

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand + React Query
- **Routing**: React Router v6
- **Animations**: Framer Motion
- **Forms**: React Hook Form with Zod validation
- **Testing**: Vitest + React Testing Library
- **PWA**: Vite PWA plugin
- **Dev Tools**: ESLint, Prettier, TypeScript

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Basic UI elements
│   ├── layout/         # Layout components
│   ├── common/         # Shared components
│   └── features/       # Feature-specific components
├── pages/              # Page components
├── hooks/              # Custom React hooks
├── services/           # API integration layer
├── stores/             # State management
├── types/              # TypeScript definitions
├── utils/              # Helper functions
└── assets/             # Static assets
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm/yarn/pnpm
- Backend API running on http://localhost:8000

### Installation

1. Clone the repository and navigate to frontend:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

4. Update environment variables in `.env`:
   ```bash
   VITE_API_BASE_URL=http://localhost:8000
   VITE_API_KEY=your-api-key
   ```

5. Start development server:
   ```bash
   npm run dev
   ```

The app will be available at http://localhost:3000

### Development Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Type checking
npm run type-check

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix
```

## API Integration

The frontend integrates with the AI Work OS backend API through a type-safe client located in `src/services/api.ts`. Key features:

- **Automatic retry logic** with exponential backoff
- **Request/response interceptors** for logging and error handling
- **Type safety** with TypeScript interfaces
- **Caching** with React Query
- **Optimistic updates** for better UX

### API Client Usage

```typescript
import { api } from '@/services/api';

// Fetch tasks
const tasks = await api.tasks.getTasks();

// Create new task
const newTask = await api.tasks.createTask({
  title: 'New Task',
  description: 'Task description',
});

// Ask AI question
const response = await api.qa.ask({
  question: 'What tasks are overdue?',
});
```

## State Management

### Global State (Zustand)

```typescript
import { useAppStore, useTheme, useTasks } from '@/stores/app-store';

// Theme management
const { mode, setMode, toggleMode } = useTheme();

// Task selection
const { selectedTaskId, setSelectedTaskId } = useTasks();

// UI state
const { sidebarCollapsed, toggleSidebar } = useUI();
```

### Server State (React Query)

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/services/api';

// Fetch data
const { data: tasks, isLoading } = useQuery({
  queryKey: ['tasks'],
  queryFn: () => api.tasks.getTasks(),
});

// Mutate data
const createTaskMutation = useMutation({
  mutationFn: api.tasks.createTask,
  onSuccess: () => {
    queryClient.invalidateQueries(['tasks']);
  },
});
```

## Component Architecture

### Design System

The app uses a consistent design system with:

- **Color palette**: Semantic color tokens
- **Typography**: Responsive font scale
- **Spacing**: 8px grid system
- **Shadows**: Layered elevation system
- **Animations**: Consistent motion language

### Component Guidelines

1. **Composition over inheritance**
2. **Props interface for all components**
3. **Consistent naming conventions**
4. **Accessibility built-in**
5. **Performance optimized**

### Example Component

```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  disabled = false,
  className,
}) => {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-md font-medium transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        {
          'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'primary',
          'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
          'border border-border hover:bg-muted': variant === 'outline',
        },
        {
          'h-8 px-3 text-sm': size === 'sm',
          'h-10 px-4': size === 'md',
          'h-12 px-6 text-lg': size === 'lg',
        },
        className
      )}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
```

## Testing

### Test Structure

```
src/
├── __tests__/          # Global tests
├── components/
│   └── __tests__/      # Component tests
├── hooks/
│   └── __tests__/      # Hook tests
└── utils/
    └── __tests__/      # Utility tests
```

### Writing Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

## Performance Optimization

### Code Splitting

- **Route-based splitting**: Each page is lazy-loaded
- **Component splitting**: Heavy components are dynamically imported
- **Library splitting**: Vendor libraries are bundled separately

### Caching Strategy

- **React Query**: Server state caching with smart invalidation
- **Browser cache**: Optimized asset caching
- **Service Worker**: Offline capability and background sync

### Bundle Optimization

- **Tree shaking**: Unused code elimination
- **Compression**: Gzip/Brotli compression
- **Preloading**: Critical resources preloaded
- **Image optimization**: WebP format with fallbacks

## Deployment

### Build Process

```bash
# Production build
npm run build

# Build with analysis
npm run build:analyze

# Preview build locally
npm run preview
```

### Environment Configuration

```bash
# Production environment variables
VITE_API_BASE_URL=https://api.aiworkos.com
VITE_API_KEY=production-api-key
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_ERROR_REPORTING=true
```

### Deployment Targets

- **Static hosting**: Vercel, Netlify, Cloudflare Pages
- **CDN**: CloudFront, Cloudflare
- **Container**: Docker with Nginx
- **Server**: Node.js with Express

## Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation
4. Use conventional commits
5. Ensure type safety

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

This project is part of AI Work OS and follows the same license terms.
import React from 'react';
import { motion, Variants, HTMLMotionProps } from 'framer-motion';
import { cn } from '@/utils/cn';

// Enhanced animation variants
export const slideVariants: Variants = {
  initial: { opacity: 0, x: -20, scale: 0.95 },
  animate: { 
    opacity: 1, 
    x: 0, 
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 30,
      duration: 0.4
    }
  },
  exit: { 
    opacity: 0, 
    x: 20, 
    scale: 0.95,
    transition: {
      type: 'tween',
      duration: 0.3
    }
  }
};

export const fadeVariants: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 25
    }
  },
  exit: { 
    opacity: 0, 
    y: -10,
    transition: { duration: 0.2 }
  }
};

export const scaleVariants: Variants = {
  initial: { opacity: 0, scale: 0.8 },
  animate: { 
    opacity: 1, 
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 500,
      damping: 30
    }
  },
  exit: { 
    opacity: 0, 
    scale: 0.8,
    transition: { duration: 0.2 }
  }
};

export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1
    }
  },
  exit: {
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1
    }
  }
};

export const bounceVariants: Variants = {
  initial: { opacity: 0, y: -100, rotate: -10 },
  animate: { 
    opacity: 1, 
    y: 0, 
    rotate: 0,
    transition: {
      type: 'spring',
      stiffness: 600,
      damping: 20,
      duration: 0.8
    }
  },
  exit: { 
    opacity: 0, 
    y: 100, 
    rotate: 10,
    transition: { duration: 0.4 }
  }
};

// Enhanced interactive button component
interface AnimatedButtonProps extends HTMLMotionProps<'button'> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  success?: boolean;
  children: React.ReactNode;
}

export const AnimatedButton: React.FC<AnimatedButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  success = false,
  children,
  className,
  disabled,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg';
  
  const variantClasses = {
    primary: 'bg-primary text-primary-foreground hover:bg-primary/90 focus:ring-primary',
    secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80 focus:ring-secondary',
    ghost: 'bg-transparent text-foreground hover:bg-muted focus:ring-muted',
    destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90 focus:ring-destructive'
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-3'
  };

  return (
    <motion.button
      className={cn(baseClasses, variantClasses[variant], sizeClasses[size], className)}
      disabled={disabled || loading}
      whileHover={{ 
        scale: disabled || loading ? 1 : 1.02,
        transition: { type: 'spring', stiffness: 400, damping: 25 }
      }}
      whileTap={{ 
        scale: disabled || loading ? 1 : 0.98,
        transition: { type: 'spring', stiffness: 400, damping: 25 }
      }}
      animate={success ? {
        scale: [1, 1.05, 1],
        transition: { duration: 0.3 }
      } : {}}
      {...props}
    >
      {loading && (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
        />
      )}
      {success && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          className="w-4 h-4"
        >
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </motion.div>
      )}
      <motion.span
        animate={loading ? { opacity: 0.6 } : { opacity: 1 }}
      >
        {children}
      </motion.span>
    </motion.button>
  );
};

// Enhanced card component with hover effects
interface AnimatedCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  selected?: boolean;
  onClick?: () => void;
}

export const AnimatedCard: React.FC<AnimatedCardProps> = ({
  children,
  className,
  hover = true,
  selected = false,
  onClick
}) => {
  return (
    <motion.div
      className={cn(
        'bg-card border rounded-lg p-4 transition-colors',
        selected 
          ? 'border-primary bg-primary/5' 
          : 'border-border hover:border-primary/50',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      whileHover={hover ? {
        y: -4,
        scale: 1.02,
        boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
        transition: { type: 'spring', stiffness: 400, damping: 25 }
      } : {}}
      whileTap={onClick ? {
        scale: 0.98,
        transition: { type: 'spring', stiffness: 400, damping: 25 }
      } : {}}
    >
      {children}
    </motion.div>
  );
};

// Enhanced tooltip component
interface AnimatedTooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
}

export const AnimatedTooltip: React.FC<AnimatedTooltipProps> = ({
  content,
  children,
  position = 'top',
  delay = 0.5
}) => {
  const [isVisible, setIsVisible] = React.useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2'
  };

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      <motion.div
        className={cn(
          'absolute z-50 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded shadow-lg whitespace-nowrap pointer-events-none',
          positionClasses[position]
        )}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={isVisible ? { 
          opacity: 1, 
          scale: 1,
          transition: { delay, type: 'spring', stiffness: 500, damping: 30 }
        } : { 
          opacity: 0, 
          scale: 0.8,
          transition: { duration: 0.1 }
        }}
      >
        {content}
      </motion.div>
    </div>
  );
};

// Progress indicator with animation
interface AnimatedProgressProps {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
  color?: string;
}

export const AnimatedProgress: React.FC<AnimatedProgressProps> = ({
  value,
  max = 100,
  className,
  showLabel = false,
  color = 'bg-primary'
}) => {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div className={cn('w-full', className)}>
      <div className="flex justify-between items-center mb-1">
        {showLabel && (
          <span className="text-sm font-medium text-foreground">
            {Math.round(percentage)}%
          </span>
        )}
      </div>
      <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
        <motion.div
          className={cn('h-full rounded-full', color)}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ 
            type: 'spring', 
            stiffness: 100, 
            damping: 15,
            duration: 1
          }}
        />
      </div>
    </div>
  );
};

// Loading skeleton with shimmer effect
interface AnimatedSkeletonProps {
  className?: string;
  lines?: number;
}

export const AnimatedSkeleton: React.FC<AnimatedSkeletonProps> = ({
  className,
  lines = 1
}) => {
  return (
    <div className={cn('animate-pulse', className)}>
      {Array.from({ length: lines }, (_, i) => (
        <motion.div
          key={i}
          className={cn(
            'bg-muted rounded',
            i === 0 ? 'h-4 w-3/4' : 'h-4 w-full mt-2',
            i === lines - 1 && lines > 1 ? 'w-1/2' : ''
          )}
          initial={{ opacity: 0.5 }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ 
            duration: 1.5, 
            repeat: Infinity, 
            ease: 'easeInOut',
            delay: i * 0.1
          }}
        />
      ))}
    </div>
  );
};

// Notification toast with animations
interface AnimatedNotificationProps {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  onClose?: () => void;
  duration?: number;
}

export const AnimatedNotification: React.FC<AnimatedNotificationProps> = ({
  type,
  title,
  message,
  onClose,
  duration = 5000
}) => {
  React.useEffect(() => {
    if (duration > 0 && onClose) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const typeStyles = {
    success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900 dark:border-green-700 dark:text-green-200',
    error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900 dark:border-red-700 dark:text-red-200',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900 dark:border-yellow-700 dark:text-yellow-200',
    info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900 dark:border-blue-700 dark:text-blue-200'
  };

  return (
    <motion.div
      className={cn(
        'border rounded-lg p-4 shadow-lg max-w-sm',
        typeStyles[type]
      )}
      initial={{ opacity: 0, y: -50, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      layout
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h4 className="font-medium">{title}</h4>
          {message && (
            <p className="text-sm mt-1 opacity-90">{message}</p>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="ml-2 opacity-60 hover:opacity-100 transition-opacity"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
      
      {duration > 0 && (
        <motion.div
          className="mt-2 h-1 bg-current opacity-20 rounded-full overflow-hidden"
          initial={{ scaleX: 1 }}
          animate={{ scaleX: 0 }}
          transition={{ duration: duration / 1000, ease: 'linear' }}
          style={{ transformOrigin: 'left' }}
        />
      )}
    </motion.div>
  );
};
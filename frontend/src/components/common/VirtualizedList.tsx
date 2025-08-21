import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion } from 'framer-motion';

interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  className?: string;
  overscan?: number; // Number of extra items to render outside visible area
  gap?: number; // Gap between items
}

export function VirtualizedList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  className = '',
  overscan = 3,
  gap = 0
}: VirtualizedListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  const totalHeight = items.length * (itemHeight + gap);

  const visibleRange = useMemo(() => {
    const visibleItemCount = Math.ceil(containerHeight / (itemHeight + gap));
    const startIndex = Math.floor(scrollTop / (itemHeight + gap));
    const endIndex = Math.min(
      items.length - 1,
      startIndex + visibleItemCount + overscan
    );

    return {
      startIndex: Math.max(0, startIndex - overscan),
      endIndex,
    };
  }, [scrollTop, containerHeight, itemHeight, gap, items.length, overscan]);

  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.startIndex, visibleRange.endIndex + 1);
  }, [items, visibleRange.startIndex, visibleRange.endIndex]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  const offsetY = visibleRange.startIndex * (itemHeight + gap);

  return (
    <div
      ref={scrollElementRef}
      className={`overflow-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map((item, index) => {
            const actualIndex = visibleRange.startIndex + index;
            return (
              <div
                key={actualIndex}
                style={{
                  height: itemHeight,
                  marginBottom: gap,
                }}
              >
                {renderItem(item, actualIndex)}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Specialized component for task lists with animations
interface VirtualizedTaskListProps<T> {
  tasks: T[];
  itemHeight: number;
  containerHeight: number;
  renderTask: (task: T, index: number) => React.ReactNode;
  className?: string;
  gap?: number;
  enableAnimations?: boolean;
}

export function VirtualizedTaskList<T>({
  tasks,
  itemHeight,
  containerHeight,
  renderTask,
  className = '',
  gap = 16,
  enableAnimations = true
}: VirtualizedTaskListProps<T>) {
  const renderItem = (task: T, index: number) => {
    if (enableAnimations) {
      return (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          className="h-full"
        >
          {renderTask(task, index)}
        </motion.div>
      );
    }
    return renderTask(task, index);
  };

  // For small lists, use regular rendering to avoid complexity
  if (tasks.length <= 20) {
    return (
      <div className={`space-y-4 ${className}`}>
        {tasks.map((task, index) => (
          <div key={index}>{renderItem(task, index)}</div>
        ))}
      </div>
    );
  }

  return (
    <VirtualizedList
      items={tasks}
      itemHeight={itemHeight}
      containerHeight={containerHeight}
      renderItem={renderItem}
      className={className}
      gap={gap}
      overscan={5}
    />
  );
}

// Hook for calculating optimal container height
export function useVirtualizedListHeight(
  maxHeight: number,
  itemHeight: number,
  itemCount: number,
  gap: number = 0
) {
  return useMemo(() => {
    const totalNeededHeight = itemCount * (itemHeight + gap);
    return Math.min(maxHeight, totalNeededHeight);
  }, [maxHeight, itemHeight, itemCount, gap]);
}
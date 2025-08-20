import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { SystemStatus } from '@/types';

export const useSystemStatus = (refetchInterval = 60000) => {
  return useQuery<SystemStatus>({
    queryKey: ['system-status'],
    queryFn: () => api.status.getStatus(),
    refetchInterval,
    staleTime: 30000, // Consider data stale after 30 seconds
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};
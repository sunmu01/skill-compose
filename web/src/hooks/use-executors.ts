'use client';

import { useQuery } from '@tanstack/react-query';
import { executorsApi } from '@/lib/api';

// Query keys
export const executorKeys = {
  all: ['executors'] as const,
  lists: () => [...executorKeys.all, 'list'] as const,
  details: () => [...executorKeys.all, 'detail'] as const,
  detail: (name: string) => [...executorKeys.details(), name] as const,
};

// List executors
export function useExecutors() {
  return useQuery({
    queryKey: executorKeys.lists(),
    queryFn: () => executorsApi.list(),
    refetchInterval: 10000, // Refresh every 10 seconds to get status updates
  });
}

// Get executor by name
export function useExecutor(name: string) {
  return useQuery({
    queryKey: executorKeys.detail(name),
    queryFn: () => executorsApi.get(name),
    enabled: !!name,
  });
}

// Check executor health
export function useExecutorHealth(name: string) {
  return useQuery({
    queryKey: [...executorKeys.detail(name), 'health'],
    queryFn: () => executorsApi.health(name),
    enabled: !!name,
    refetchInterval: 30000, // Check health every 30 seconds
  });
}

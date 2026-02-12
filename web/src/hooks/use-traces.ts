'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tracesApi } from '@/lib/api';

// Query keys
export const traceKeys = {
  all: ['traces'] as const,
  lists: () => [...traceKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) =>
    [...traceKeys.lists(), filters] as const,
  details: () => [...traceKeys.all, 'detail'] as const,
  detail: (id: string) => [...traceKeys.details(), id] as const,
};

// List traces
export function useTraces(params?: {
  success?: boolean;
  offset?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: traceKeys.list(params || {}),
    queryFn: () => tracesApi.list(params),
  });
}

// Get trace detail
export function useTrace(id: string) {
  return useQuery({
    queryKey: traceKeys.detail(id),
    queryFn: () => tracesApi.get(id),
    enabled: !!id,
  });
}

// Delete trace
export function useDeleteTrace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => tracesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: traceKeys.lists() });
    },
  });
}

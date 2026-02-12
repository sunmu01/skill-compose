'use client';

import { useQuery } from '@tanstack/react-query';
import { toolsApi } from '@/lib/api';

// Query keys
export const toolKeys = {
  all: ['tools'] as const,
  list: (category?: string) => [...toolKeys.all, 'list', category] as const,
  detail: (id: string) => [...toolKeys.all, 'detail', id] as const,
};

// List all tools
export function useTools(category?: string) {
  return useQuery({
    queryKey: toolKeys.list(category),
    queryFn: () => toolsApi.list(category),
  });
}

// Get tool detail
export function useTool(id: string) {
  return useQuery({
    queryKey: toolKeys.detail(id),
    queryFn: () => toolsApi.get(id),
    enabled: !!id,
  });
}

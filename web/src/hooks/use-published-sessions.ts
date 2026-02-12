'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { publishedAgentApi } from '@/lib/api';

export const publishedSessionKeys = {
  all: ['published-sessions'] as const,
  lists: () => [...publishedSessionKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) =>
    [...publishedSessionKeys.lists(), filters] as const,
  details: () => [...publishedSessionKeys.all, 'detail'] as const,
  detail: (id: string) => [...publishedSessionKeys.details(), id] as const,
};

export function usePublishedSessions(params?: {
  agentId?: string;
  offset?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: publishedSessionKeys.list(params || {}),
    queryFn: () =>
      publishedAgentApi.listAllSessions({
        agent_id: params?.agentId,
        offset: params?.offset,
        limit: params?.limit,
      }),
  });
}

export function usePublishedSessionDetail(sessionId: string) {
  return useQuery({
    queryKey: publishedSessionKeys.detail(sessionId),
    queryFn: () => publishedAgentApi.getSessionDetail(sessionId),
    enabled: !!sessionId,
  });
}

export function useDeletePublishedSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => publishedAgentApi.deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: publishedSessionKeys.lists() });
    },
  });
}

export function useDeleteAllAgentSessions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (agentId: string) => publishedAgentApi.deleteAgentSessions(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: publishedSessionKeys.lists() });
    },
  });
}

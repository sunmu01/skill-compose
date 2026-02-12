'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentPresetsApi } from '@/lib/api';
import type { AgentPresetCreateRequest, AgentPresetUpdateRequest } from '@/lib/api';

// Query keys
export const agentPresetKeys = {
  all: ['agent-presets'] as const,
  lists: () => [...agentPresetKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) =>
    [...agentPresetKeys.lists(), filters] as const,
  details: () => [...agentPresetKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentPresetKeys.details(), id] as const,
};

// List agent presets
export function useAgentPresets(params?: { is_system?: boolean }) {
  return useQuery({
    queryKey: agentPresetKeys.list(params || {}),
    queryFn: () => agentPresetsApi.list(params),
  });
}

// Get agent preset by ID
export function useAgentPreset(id: string) {
  return useQuery({
    queryKey: agentPresetKeys.detail(id),
    queryFn: () => agentPresetsApi.get(id),
    enabled: !!id,
  });
}

// Create agent preset
export function useCreateAgentPreset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AgentPresetCreateRequest) => agentPresetsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentPresetKeys.lists() });
    },
  });
}

// Update agent preset
export function useUpdateAgentPreset(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AgentPresetUpdateRequest) => agentPresetsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentPresetKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: agentPresetKeys.lists() });
    },
  });
}

// Delete agent preset
export function useDeleteAgentPreset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => agentPresetsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentPresetKeys.lists() });
    },
  });
}

// Publish agent preset
export function usePublishAgent(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { api_response_mode: 'streaming' | 'non_streaming' }) =>
      agentPresetsApi.publish(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentPresetKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: agentPresetKeys.lists() });
    },
  });
}

// Unpublish agent preset
export function useUnpublishAgent(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => agentPresetsApi.unpublish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentPresetKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: agentPresetKeys.lists() });
    },
  });
}

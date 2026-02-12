'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { backupApi } from '@/lib/api';

export const backupKeys = {
  all: ['backups'] as const,
  list: () => [...backupKeys.all, 'list'] as const,
};

export function useBackupList() {
  return useQuery({
    queryKey: backupKeys.list(),
    queryFn: () => backupApi.list(),
  });
}

export function useCreateBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params?: { includeEnv?: boolean }) => backupApi.create(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: backupKeys.list() });
    },
  });
}

export function useRestoreFromUpload() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => backupApi.restoreFromUpload(file),
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });
}

export function useRestoreFromServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (filename: string) => backupApi.restoreFromServer(filename),
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });
}

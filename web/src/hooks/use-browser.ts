'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { browserApi, BrowserDirectoryContents, BrowserFilePreview, BrowserFileEntry } from '@/lib/api';

export function useDirectoryListing(path: string) {
  return useQuery<BrowserDirectoryContents>({
    queryKey: ['browser', 'directory', path],
    queryFn: () => browserApi.listDirectory(path),
  });
}

export function useFilePreview(path: string | null) {
  return useQuery<BrowserFilePreview>({
    queryKey: ['browser', 'preview', path],
    queryFn: () => browserApi.previewFile(path!),
    enabled: !!path,
  });
}

export function useUploadFile() {
  const queryClient = useQueryClient();

  return useMutation<BrowserFileEntry, Error, { targetPath: string; file: File }>({
    mutationFn: ({ targetPath, file }) => browserApi.uploadFile(targetPath, file),
    onSuccess: (_, variables) => {
      // Invalidate the directory listing to refresh
      queryClient.invalidateQueries({ queryKey: ['browser', 'directory', variables.targetPath] });
    },
  });
}

export function useDeleteFile() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { path: string; parentPath: string }>({
    mutationFn: ({ path }) => browserApi.deleteFile(path),
    onSuccess: (_, variables) => {
      // Invalidate the parent directory listing to refresh
      queryClient.invalidateQueries({ queryKey: ['browser', 'directory', variables.parentPath] });
    },
  });
}

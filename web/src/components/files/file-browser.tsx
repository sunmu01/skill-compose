'use client';

import { useState, useMemo } from 'react';
import { useDirectoryListing } from '@/hooks/use-browser';
import { BrowserFileEntry } from '@/lib/api';
import { FileBreadcrumbs } from './file-breadcrumbs';
import { FileToolbar } from './file-toolbar';
import { FileList } from './file-list';
import { FilePreview } from './file-preview';
import { UploadDialog } from './upload-dialog';
import { Card, CardContent } from '@/components/ui/card';
import { Spinner } from '@/components/ui/spinner';
import { AlertCircle } from 'lucide-react';

export type SortOption = 'name-asc' | 'name-desc' | 'modified-newest' | 'modified-oldest' | 'size-largest' | 'size-smallest';

function sortEntries(entries: BrowserFileEntry[], sortBy: SortOption): BrowserFileEntry[] {
  return [...entries].sort((a, b) => {
    if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
    switch (sortBy) {
      case 'name-asc': return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
      case 'name-desc': return b.name.localeCompare(a.name, undefined, { sensitivity: 'base' });
      case 'modified-newest': return new Date(b.modified_at).getTime() - new Date(a.modified_at).getTime();
      case 'modified-oldest': return new Date(a.modified_at).getTime() - new Date(b.modified_at).getTime();
      case 'size-largest': return (b.size ?? 0) - (a.size ?? 0);
      case 'size-smallest': return (a.size ?? 0) - (b.size ?? 0);
    }
  });
}

export function FileBrowser() {
  const [currentPath, setCurrentPath] = useState('');
  const [selectedFile, setSelectedFile] = useState<BrowserFileEntry | null>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [sortBy, setSortBy] = useState<SortOption>('name-asc');

  const { data, isLoading, error, refetch, isFetching } = useDirectoryListing(currentPath);

  const sortedEntries = useMemo(
    () => sortEntries(data?.entries || [], sortBy),
    [data?.entries, sortBy]
  );

  const handleNavigate = (path: string) => {
    setCurrentPath(path);
    setSelectedFile(null);
  };

  const handleSelect = (entry: BrowserFileEntry) => {
    if (entry.type === 'file') {
      setSelectedFile(entry);
    }
  };

  const handleNavigateUp = () => {
    if (data?.parent_path !== null && data?.parent_path !== undefined) {
      setCurrentPath(data.parent_path);
      setSelectedFile(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-200px)]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)] text-muted-foreground">
        <AlertCircle className="h-12 w-12 mb-4 text-destructive" />
        <p className="text-lg font-medium">Failed to load directory</p>
        <p className="text-sm">{error instanceof Error ? error.message : 'Unknown error'}</p>
      </div>
    );
  }

  return (
    <div className="flex gap-4 h-[calc(100vh-200px)]">
      {/* Main file list */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between mb-4 gap-4">
          <FileBreadcrumbs
            breadcrumbs={data?.breadcrumbs || []}
            onNavigate={handleNavigate}
          />
          <FileToolbar
            currentPath={currentPath}
            parentPath={data?.parent_path ?? null}
            onRefresh={() => refetch()}
            onNavigateUp={handleNavigateUp}
            onUploadClick={() => setUploadDialogOpen(true)}
            isRefreshing={isFetching}
            sortBy={sortBy}
            onSortChange={setSortBy}
          />
        </div>

        <Card className="flex-1 overflow-hidden">
          <CardContent className="p-4 h-full overflow-auto">
            <FileList
              entries={sortedEntries}
              selectedPath={selectedFile?.path || null}
              onSelect={handleSelect}
              onNavigate={handleNavigate}
            />
          </CardContent>
        </Card>
      </div>

      {/* Preview panel */}
      {selectedFile && (
        <div className="w-[400px] flex-shrink-0">
          <FilePreview
            file={selectedFile}
            onClose={() => setSelectedFile(null)}
          />
        </div>
      )}

      {/* Upload dialog */}
      <UploadDialog
        open={uploadDialogOpen}
        onOpenChange={setUploadDialogOpen}
        targetPath={currentPath}
      />
    </div>
  );
}
